import base64
import binascii
from functools import cached_property

from rest_framework import generics
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from desecapi import metrics
from desecapi.authentication import (
    BasicTokenAuthentication,
    TokenAuthentication,
    URLParamAuthentication,
)
from desecapi.exceptions import ConcurrencyException
from desecapi.models import Domain
from desecapi.pdns_change_tracker import PDNSChangeTracker
from desecapi.permissions import TokenHasDomainDynDNSPermission
from desecapi.renderers import PlainTextRenderer
from desecapi.serializers import RRsetSerializer


class DynDNS12UpdateView(generics.GenericAPIView):
    authentication_classes = (
        TokenAuthentication,
        BasicTokenAuthentication,
        URLParamAuthentication,
    )
    permission_classes = (TokenHasDomainDynDNSPermission,)
    renderer_classes = [PlainTextRenderer]
    serializer_class = RRsetSerializer
    throttle_scope = "dyndns"

    @property
    def throttle_scope_bucket(self):
        return self.domain.name

    def _find_ip(self, params, version):
        if version == 4:
            look_for = "."
        elif version == 6:
            look_for = ":"
        else:
            raise Exception

        # Check URL parameters
        for p in params:
            if p in self.request.query_params:
                if not len(self.request.query_params[p]):
                    return None
                if look_for in self.request.query_params[p]:
                    return self.request.query_params[p]

        # Check remote IP address
        client_ip = self.request.META.get("REMOTE_ADDR")
        if look_for in client_ip:
            return client_ip

        # give up
        return None

    @cached_property
    def qname(self):
        # hostname parameter
        try:
            if self.request.query_params["hostname"] != "YES":
                return self.request.query_params["hostname"].lower()
        except KeyError:
            pass

        # host_id parameter
        try:
            return self.request.query_params["host_id"].lower()
        except KeyError:
            pass

        # http basic auth username
        try:
            domain_name = (
                base64.b64decode(
                    get_authorization_header(self.request)
                    .decode()
                    .split(" ")[1]
                    .encode()
                )
                .decode()
                .split(":")[0]
            )
            if domain_name and "@" not in domain_name:
                return domain_name.lower()
        except (binascii.Error, IndexError, UnicodeDecodeError):
            pass

        # username parameter
        try:
            return self.request.query_params["username"].lower()
        except KeyError:
            pass

        # only domain associated with this user account
        try:
            return self.request.user.domains.get().name
        except Domain.MultipleObjectsReturned:
            raise ValidationError(
                detail={
                    "detail": "Request does not properly specify domain for update.",
                    "code": "domain-unspecified",
                }
            )
        except Domain.DoesNotExist:
            metrics.get("desecapi_dynDNS12_domain_not_found").inc()
            raise NotFound("nohost")

    @cached_property
    def domain(self):
        try:
            return Domain.objects.filter_qname(
                self.qname, owner=self.request.user
            ).order_by("-name_length")[0]
        except (IndexError, ValueError):
            raise NotFound("nohost")

    @property
    def subname(self):
        return self.qname.rpartition(f".{self.domain.name}")[0]

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            "domain": self.domain,
            "minimum_ttl": 60,
        }

    def get_queryset(self):
        return self.domain.rrset_set.filter(
            subname=self.subname, type__in=["A", "AAAA"]
        )

    def get(self, request, *args, **kwargs):
        instances = self.get_queryset().all()

        ipv4 = self._find_ip(["myip", "myipv4", "ip"], version=4)
        ipv6 = self._find_ip(["myipv6", "ipv6", "myip", "ip"], version=6)

        data = [
            {
                "type": "A",
                "subname": self.subname,
                "ttl": 60,
                "records": [ipv4] if ipv4 else [],
            },
            {
                "type": "AAAA",
                "subname": self.subname,
                "ttl": 60,
                "records": [ipv6] if ipv6 else [],
            },
        ]

        serializer = self.get_serializer(instances, data=data, many=True, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            if any(
                any(
                    getattr(non_field_error, "code", "") == "unique"
                    for non_field_error in err.get("non_field_errors", [])
                )
                for err in e.detail
            ):
                raise ConcurrencyException from e
            raise e

        with PDNSChangeTracker():
            serializer.save()

        return Response("good", content_type="text/plain")

/* eslint-env node */

/** @type {import('eslint').Linter.Config} */
module.exports = {
  root: true,
  env: {
    browser: true,
    node: true, // Can be removed after migration to vite.
    es2022: true,
  },
  extends: [
    'plugin:vue/essential',
    // 'plugin:vue/strongly-recommended',
    // 'plugin:vue/recommended',
    'plugin:vuetify/base',
    'eslint:recommended'
  ],
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'vue/v-bind-style': 'warn',
    'vue/v-on-style': 'warn',
    'vue/v-slot-style': 'warn',
    'vue/mustache-interpolation-spacing': ['warn', 'always'],
    'vue/no-multi-spaces': 'warn',
    'vue/no-deprecated-filter': 'warn', // Preparation for vue3
    'vue/no-deprecated-v-on-number-modifiers': 'warn', // Preparation for vue3
    'vue/no-deprecated-html-element-is': 'warn', // Preparation for vue3
  },
  ignorePatterns: ['**/src/modules/**/*'],
}

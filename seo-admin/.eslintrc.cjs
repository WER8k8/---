module.exports = {
  root: true,
  env: {
    node: true,
    browser: true,
    es2021: true
  },
  extends: [
    'plugin:vue/vue3-essential',
    'eslint:recommended'
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    parser: '@typescript-eslint/parser',
    sourceType: 'module'
  },
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'vue/multi-word-component-names': 'off',
    'vue/no-unused-components': 'warn',
    // 'vue/no-unused-vars': 'warn',
    // 'no-unused-vars': 'warn',
    'vue/require-default-prop': 'off',
    'vue/require-explicit-emits': 'off',
    'vue/no-setup-props-destructure': 'off',
    'vue/component-definition-name-casing': ['error', 'PascalCase'],
    'vue/html-closing-bracket-newline': ['error', {
      'singleline': 'never',
      'multiline': 'always'
    }],
    'vue/html-closing-bracket-spacing': ['error', {
      'startTag': 'never',
      'endTag': 'never',
      'selfClosingTag': 'always'
    }],
    // 'vue/html-indent': ['error', 2, {
    //   'attribute': 1,
    //   'baseIndent': 0,
    //   'closeBracket': 0,
    //   'alignAttributesVertically': true,
    //   'ignores': []
    // }],
    // 'vue/max-attributes-per-line': ['error', {
    //   'singleline': 3,
    //   'multiline': 1
    // }],
    'vue/html-quotes': ['error', 'double'],
    'vue/no-spaces-around-equal-signs-in-attribute': 'error',
    'vue/attribute-hyphenation': ['error', 'always'],
    'vue/v-bind-style': ['error', 'shorthand'],
    'vue/v-on-style': ['error', 'shorthand'],
    'vue/html-self-closing': ['error', {
      'html': {
        'void': 'always',
        'normal': 'any',
        'component': 'always'
      },
      'svg': 'always',
      'math': 'always'
    }],
    // 'vue/component-name-casing': ['error', 'PascalCase'],
    // 'vue/component-api-style': ['error', ['composition']],
    // 'vue/component-tags-order': ['error', {
    //   'order': ['script', 'template', 'style']
    // }],
    'vue/no-parsing-error': 'error'
  },
  globals: {
    defineProps: 'readonly',
    defineEmits: 'readonly',
    defineExpose: 'readonly',
    withDefaults: 'readonly'
  }
}
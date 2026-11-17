export default [
  {
    ignores: ["node_modules/**", ".venv/**"],
  },
  {
    files: ["app/static/**/*.js"],
    languageOptions: {
      globals: {
        document: "readonly"
      }
    },
    rules: {
      "no-unused-vars": "error",
      "no-undef": "error"
    }
  }
];

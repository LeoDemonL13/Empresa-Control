import js from '@eslint/js'
import globals from 'globals'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'

                                    
  
                                                                         
                                                                         
                                                                       
                                                                              
                                                
export default [
  { ignores: ['dist/**', 'dev-dist/**', 'node_modules/**', 'public/**'] },

  js.configs.recommended,

  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: { ...globals.browser, ...globals.es2021 },
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    settings: { react: { version: 'detect' } },
    plugins: {
      react,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...react.configs.flat.recommended.rules,
      ...react.configs.flat['jsx-runtime'].rules,
      ...reactHooks.configs.recommended.rules,

                                                                             
                                                       
      'react/prop-types': 'off',
                                                                            
                                                                     
      'react/no-unescaped-entities': 'off',

                                                                             
                                                                            
                                                                         
                                                                       
                                                                       
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',

                                                                               
                                                                              
                                                                             
                                                                               
                                                                              
                                                                              
                                                                          
                                                                              
                                                                           
                     
      'react-hooks/set-state-in-effect': 'warn',
      'react-hooks/refs': 'warn',
      'react-hooks/static-components': 'warn',
      'react-hooks/purity': 'warn',
      'react-hooks/immutability': 'warn',
      'react-hooks/use-memo': 'warn',

                                                
      'no-useless-assignment': 'warn',

                                                                           
                                                                             
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],

                                                                            
                                                         
      'no-unused-vars': ['warn', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        caughtErrors: 'none',
        ignoreRestSiblings: true,
      }],
      'no-empty': ['warn', { allowEmptyCatch: true }],
    },
  },

                                         
  {
    files: ['**/*.test.{js,jsx}', 'src/test/**/*.{js,jsx}'],
    languageOptions: {
      globals: { ...globals.browser, ...globals.node, ...globals.vitest },
    },
  },

                                                                             
  {
    files: ['*.config.js', 'vite.config.js', 'vitest.config.js', 'postcss.config.js', 'tailwind.config.js'],
    languageOptions: { globals: { ...globals.node } },
  },
]

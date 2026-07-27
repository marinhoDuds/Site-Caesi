
declare module '*.vue' {
  import type { Component } from 'vue'

  const component: Component
  export default component
}

declare module '*.svg?raw' {
  const content: string
  export default content
}

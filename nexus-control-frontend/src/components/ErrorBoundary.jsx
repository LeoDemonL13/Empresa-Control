import { Component } from 'react'

export default class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex h-full items-center justify-center bg-obsidian-main p-6">
          <div className="nx-surface max-w-sm text-center">
            <p className="text-base font-semibold text-ink-900 dark:text-white">Algo salió mal</p>
            <p className="mt-1 text-sm text-ink-500 dark:text-obsidian-muted">
              Recarga la página. Si el problema sigue, contacta al súper administrador.
            </p>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

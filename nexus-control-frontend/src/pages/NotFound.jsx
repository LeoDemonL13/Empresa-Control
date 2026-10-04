import { Link } from 'react-router-dom'
import { Button } from '../components/ui'

export default function NotFound() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 py-16 text-center">
      <p className="font-mono text-sm text-ink-400 dark:text-obsidian-muted">404</p>
      <h1 className="text-xl font-semibold text-ink-900 dark:text-white">Página no encontrada</h1>
      <Link to="/">
        <Button size="sm">Volver al inicio</Button>
      </Link>
    </div>
  )
}

import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import { useAuth } from '../context/AuthContext'

export default function Layout() {
  const { user } = useAuth()

  return (
    <div className="flex h-screen overflow-hidden bg-ink-50 dark:bg-obsidian-main">
      <Sidebar role={user?.role} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto scrollbar-thin p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

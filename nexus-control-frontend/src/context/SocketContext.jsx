import { createContext, useContext, useEffect, useRef, useState } from 'react'
import { io } from 'socket.io-client'
import { useAuth } from './AuthContext'

const SocketContext = createContext(null)

export function SocketProvider({ children }) {
  const { token, user, logout } = useAuth()
  const [socket, setSocket] = useState(null)
  const tokenRef = useRef(token)

  useEffect(() => {
    tokenRef.current = token
  }, [token])

  useEffect(() => {
    if (!user) {
      setSocket(null)
      return undefined
    }

    const s = io({
      transports: ['websocket', 'polling'],
      auth: (cb) => cb({ token: tokenRef.current }),
    })

    s.on('auth:forzar_logout', () => {
      logout()
    })

    setSocket(s)

    return () => {
      s.disconnect()
    }
  }, [user?.id, logout])

  return <SocketContext.Provider value={socket}>{children}</SocketContext.Provider>
}

export function useSocket() {
  return useContext(SocketContext)
}

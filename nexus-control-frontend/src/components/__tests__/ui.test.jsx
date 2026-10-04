import { render, screen } from '@testing-library/react'
import { Button, Badge } from '../ui'

describe('Button', () => {
  it('el botón primario es una píldora con el acento', () => {
    render(<Button>Guardar</Button>)
    const boton = screen.getByRole('button', { name: 'Guardar' })
    expect(boton.className).toContain('rounded-full')
    expect(boton.className).toContain('bg-accent')
  })

  it('el botón en carga queda deshabilitado', () => {
    render(<Button loading>Guardando</Button>)
    expect(screen.getByRole('button', { name: 'Guardando' })).toBeDisabled()
  })
})

describe('Badge', () => {
  it('muestra el punto de estado cuando se pide', () => {
    render(<Badge tone="success" dot>En línea</Badge>)
    expect(screen.getByText('En línea')).toBeInTheDocument()
  })
})

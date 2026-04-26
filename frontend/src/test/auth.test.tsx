import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider, useAuth } from '../context/AuthContext'
import { tokenStorage } from '../services/api'

vi.mock('../services/api', async () => {
  const actual = await vi.importActual<any>('../services/api')
  return {
    ...actual,
    authApi: {
      login: vi.fn(),
      me: vi.fn(),
      changePassword: vi.fn(),
      listUsers: vi.fn(),
      createUser: vi.fn(),
      updateUser: vi.fn(),
      deleteUser: vi.fn(),
      auditLog: vi.fn(),
    },
  }
})

import { authApi } from '../services/api'

function Probe() {
  const { user, hasRole } = useAuth()
  return (
    <div>
      <div data-testid="user">{user?.username || 'anon'}</div>
      <div data-testid="is-admin">{String(hasRole('admin'))}</div>
      <div data-testid="manager-fallback">{String(hasRole('manager'))}</div>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    tokenStorage.clear()
    vi.clearAllMocks()
  })

  it('starts anonymous when there is no token', async () => {
    render(
      <BrowserRouter>
        <AuthProvider><Probe /></AuthProvider>
      </BrowserRouter>
    )
    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('anon')
    })
  })

  it('loads user when valid token is stored', async () => {
    tokenStorage.set('fake-token')
    ;(authApi.me as any).mockResolvedValueOnce({
      data: { id: 1, username: 'admin', role: 'admin', is_active: true, created_at: '2025-01-01' },
    })

    render(
      <BrowserRouter>
        <AuthProvider><Probe /></AuthProvider>
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('admin')
      expect(screen.getByTestId('is-admin')).toHaveTextContent('true')
      // admin debe pasar todo hasRole
      expect(screen.getByTestId('manager-fallback')).toHaveTextContent('true')
    })
  })
})

import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import JigsawDemo from '@/demo/JigsawDemo'

export default function DemoPage() {
  const navigate = useNavigate()

  useEffect(() => {
    // Check if user is authenticated
    const isAuthenticated = sessionStorage.getItem('demo_authenticated') === 'true'
    if (!isAuthenticated) {
      navigate('/demo/auth')
    }
  }, [navigate])

  // Get backend URL from environment or use default
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:3001'

  return (
    <div className="h-screen w-screen overflow-hidden">
      <JigsawDemo backendUrl={backendUrl} />
    </div>
  )
}


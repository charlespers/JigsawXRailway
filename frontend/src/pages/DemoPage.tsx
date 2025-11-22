import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import JigsawDemo from '@/demo/JigsawDemo'
import configService from '@/demo/services/config'

export default function DemoPage() {
  const navigate = useNavigate()

  useEffect(() => {
    // Check if user is authenticated
    const isAuthenticated = sessionStorage.getItem('demo_authenticated') === 'true'
    if (!isAuthenticated) {
      navigate('/demo/auth')
    }
  }, [navigate])

  // Get backend URL from config service
  const backendUrl = configService.getBackendUrl()

  return (
    <div className="h-screen w-screen overflow-hidden">
      <JigsawDemo backendUrl={backendUrl} />
    </div>
  )
}


import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { OpportunityFeed } from './pages/OpportunityFeed'
import { OpportunityDetail } from './pages/OpportunityDetail'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<OpportunityFeed />} />
          <Route path="/opportunity/:id" element={<OpportunityDetail />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App

import { BrowserRouter } from 'react-router-dom'

import { AppRouter } from './routers/router.jsx'
import { AuthProvider } from './providers/AuthProvider.jsx'

function App() {
	return (
		<BrowserRouter>
			<AuthProvider>
				<AppRouter />
			</AuthProvider>
		</BrowserRouter>
	)
}

export default App

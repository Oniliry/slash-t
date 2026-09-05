import { BrowserRouter } from 'react-router-dom'

import { AppRouter } from './routers/router.jsx'

function App() {
	return (
		<BrowserRouter>
			<AppRouter />
		</BrowserRouter>
	)
}

export default App


import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { DebugSessionProvider } from './context/DebugSessionContext';
import { AppLayout } from './layouts/AppLayout';
import { Dashboard } from './pages/Dashboard';

import { Repositories } from './pages/Repositories';
import { Investigations } from './pages/Investigations';

function App() {
  return (
    <ThemeProvider>
      <DebugSessionProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<AppLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="repositories" element={<Repositories />} />
              <Route path="investigations" element={<Investigations />}>
                <Route path=":sessionId" element={<Investigations />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </DebugSessionProvider>
    </ThemeProvider>
  );
}

export default App;

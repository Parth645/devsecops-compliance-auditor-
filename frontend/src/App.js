import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import RepositoryScanner from './components/RepositoryScanner';
import ScanResults from './components/ScanResults';
import ScanHistory from './components/ScanHistory';
import ComplianceRules from './components/ComplianceRules';
import { AppProvider } from './context/AppContext';

function App() {
  return (
    <AppProvider>
      <Router>
        <div className="App">
          <Navbar />
          <main style={{ paddingTop: '80px', minHeight: '100vh' }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/scan" element={<RepositoryScanner />} />
              <Route path="/results/:scanId?" element={<ScanResults />} />
              <Route path="/history" element={<ScanHistory />} />
              <Route path="/rules" element={<ComplianceRules />} />
            </Routes>
          </main>
          <ToastContainer
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme="light"
          />
        </div>
      </Router>
    </AppProvider>
  );
}

export default App;

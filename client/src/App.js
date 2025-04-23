import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { supabase } from './supabase';
import Login from './Login';
import PermitList from './PermitList'; // we'll scaffold this next

function ProtectedRoute({ children }) {
  const [session, setSession] = useState(null);

  useEffect(() => {
    const s = supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data: listener } = supabase.auth.onAuthStateChange((_, session) => {
      setSession(session);
    });
    return () => listener.subscription.unsubscribe();
  }, []);

  if (session === null) {
    // still loading
    return null;
  }

  if (!session) {
    // not logged in
    return <Navigate to="/login" replace />;
  }

  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/permits"
          element={
            <ProtectedRoute>
              <PermitList />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/permits" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
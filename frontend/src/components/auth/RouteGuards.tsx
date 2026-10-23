import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface RouteGuardProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<RouteGuardProps> = ({ children }) => {
  const { isAuthenticated, loadingUser } = useAuth();
  const location = useLocation();

  if (loadingUser) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-200">
        <LoadingSpinner message="Verifying session..." fullHeight />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/signin" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

export const AdminRoute: React.FC<RouteGuardProps> = ({ children }) => {
  const { isAuthenticated, isAdmin, loadingUser } = useAuth();
  const location = useLocation();

  if (loadingUser) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-200">
        <LoadingSpinner message="Verifying administrator permissions..." fullHeight />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/signin" state={{ from: location }} replace />;
  }

  if (!isAdmin) {
    return <Navigate to="/app" replace />;
  }

  return <>{children}</>;
};

export const PublicOnlyRoute: React.FC<RouteGuardProps> = ({ children }) => {
  const { isAuthenticated, isAdmin, loadingUser } = useAuth();

  if (loadingUser) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-200">
        <LoadingSpinner message="Loading..." fullHeight />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to={isAdmin ? '/admin' : '/app'} replace />;
  }

  return <>{children}</>;
};

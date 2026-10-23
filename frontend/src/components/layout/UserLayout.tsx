import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { UserSidebar } from './UserSidebar';
import { UserHeader } from './UserHeader';
import { DemoEnvironmentBanner } from '../common/DemoEnvironmentBanner';

export const UserLayout: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex">
      {/* Sidebar navigation */}
      <UserSidebar mobileOpen={mobileOpen} onCloseMobile={() => setMobileOpen(false)} />

      {/* Main content wrapper */}
      <div className="flex-1 lg:pl-72 flex flex-col min-w-0">
        <DemoEnvironmentBanner />
        <UserHeader onOpenMobile={() => setMobileOpen(true)} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};


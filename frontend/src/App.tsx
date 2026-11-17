import React, { useState } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { TopBar } from './components/layout/TopBar';
import { CommandCenter } from './pages/CommandCenter';
import { ThreatDetection } from './pages/ThreatDetection';
import { Investigations } from './pages/Investigations';
import { EvidenceExplorer } from './pages/EvidenceExplorer';
import { ResponseCenter } from './pages/ResponseCenter';
import { Reports } from './pages/Reports';
import { Telemetry } from './pages/Telemetry';
import { Settings } from './pages/Settings';
import { DemoScenarioModal } from './components/investigation/DemoScenarioModal';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('command-center');
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [demoModalOpen, setDemoModalOpen] = useState<boolean>(false);

  // Cross-page state transitions
  const [targetInvestigationId, setTargetInvestigationId] = useState<string | null>(null);
  const [threatFilter, setThreatFilter] = useState<{ severity?: string; method?: string } | undefined>();

  const handleNavigate = (tab: string, state?: any) => {
    if (state?.investigationId) {
      setTargetInvestigationId(state.investigationId);
    }
    if (state?.severity || state?.method) {
      setThreatFilter({ severity: state.severity, method: state.method });
    }
    setCurrentTab(tab);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleScenarioInvestigationLaunch = (invId: string) => {
    setTargetInvestigationId(invId);
    setCurrentTab('investigations');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-obsidian text-ivory scanlines">
      {/* Sidebar Navigation */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={handleNavigate}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Real-Time Status Bar */}
        <TopBar
          onOpenSettings={() => setCurrentTab('settings')}
        />

        {/* Dynamic Page Viewport */}
        <main className="flex-1 overflow-y-auto bg-obsidian relative bg-tech-grid">
          {currentTab === 'command-center' && (
            <CommandCenter
              onNavigate={handleNavigate}
              onOpenDemoWizard={() => setDemoModalOpen(true)}
            />
          )}

          {currentTab === 'threat-detection' && (
            <ThreatDetection
              onNavigate={handleNavigate}
              initialFilter={threatFilter}
            />
          )}

          {currentTab === 'investigations' && (
            <Investigations
              onNavigate={handleNavigate}
              targetInvestigationId={targetInvestigationId}
            />
          )}

          {currentTab === 'evidence-explorer' && (
            <EvidenceExplorer
              initialInvestigationId={targetInvestigationId}
            />
          )}

          {currentTab === 'response-center' && (
            <ResponseCenter
              initialInvestigationId={targetInvestigationId}
            />
          )}

          {currentTab === 'reports' && (
            <Reports
              initialInvestigationId={targetInvestigationId}
            />
          )}

          {currentTab === 'telemetry' && (
            <Telemetry />
          )}

          {currentTab === 'settings' && (
            <Settings />
          )}
        </main>
      </div>

      {/* Demo Scenario Modal Wizard */}
      <DemoScenarioModal
        isOpen={demoModalOpen}
        onClose={() => setDemoModalOpen(false)}
        onLaunchInvestigation={handleScenarioInvestigationLaunch}
        onGoToTelemetry={() => setCurrentTab('telemetry')}
      />
    </div>
  );
};

export default App;

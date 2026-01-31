import { useState, useEffect } from 'react';
import AdminCabinet from './AdminCabinet.jsx';
import OperationsPanel from './OperationsPanel.jsx';

const Operations = () => {
  const [activeTab, setActiveTab] = useState('admin');
  useEffect(() => {
    const hash = window.location.hash.slice(1).toLowerCase();
    if (hash === 'operations') setActiveTab('operations');
    const onHashChange = () => {
      const h = window.location.hash.slice(1).toLowerCase();
      if (h === 'operations') setActiveTab('operations');
    };
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  return (
    <section id="operations" className="section reveal is-hidden" data-admin-only>
      <div className="section-header-row">
        <div className="section-heading">
          <h2>Operations &amp; Admin cabinet</h2>
          <p>Admin: view and manage users, drivers, events. Operations: create participations and incidents.</p>
        </div>
        <nav className="ops-tabs" role="tablist" aria-label="Admin or Operations">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'admin'}
            className={activeTab === 'admin' ? 'btn primary' : 'btn ghost'}
            onClick={() => setActiveTab('admin')}
          >
            Admin
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'operations'}
            className={activeTab === 'operations' ? 'btn primary' : 'btn ghost'}
            onClick={() => setActiveTab('operations')}
          >
            Operations
          </button>
        </nav>
      </div>

      <div hidden={activeTab !== 'admin'} style={activeTab !== 'admin' ? { display: 'none' } : undefined}>
        <AdminCabinet />
      </div>
      <div hidden={activeTab !== 'operations'} style={activeTab !== 'operations' ? { display: 'none' } : undefined}>
        <OperationsPanel />
      </div>
    </section>
  );
};

export default Operations;

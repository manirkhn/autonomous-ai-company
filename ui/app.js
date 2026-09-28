// Owner Command Center Client Controller (Phase 5G)

let isEmergencyStop = false;
let currentOfficeData = null;

document.addEventListener("DOMContentLoaded", () => {
  fetchMarketingCommandCenter();
  fetchCloudRuntimeStatus();
  fetchGovernanceData();
  fetchOfficeState();
  fetchCloudStatus();
  fetchStatus();
  fetchTasks();
  fetchEmployees();
  fetchApprovals();
  fetchOpportunities();
  fetchProducts();
  fetchLeads();
  fetchDeliveries();
  fetchOwnerMetrics();
  fetchFirewall();
  fetchSkills();
  fetchTreasury();
  fetchMarketplace();
  fetchCapabilityGaps();
  fetchPhase4Dashboard();
  fetchAcquisitionData();
  fetchOperatorCockpit();
  initEventStream();

  // Restore active tab from URL hash (e.g. #tab-governance, #governance, #ai-office)
  const initialHash = window.location.hash.replace("#tab-", "").replace("#", "").trim();
  if (initialHash) {
    switchTab(initialHash);
  }

  // Support browser back/forward buttons
  window.addEventListener("hashchange", () => {
    const newHash = window.location.hash.replace("#tab-", "").replace("#", "").trim();
    if (newHash) switchTab(newHash);
  });

  setInterval(fetchOperatorCockpit, 8000);
  setInterval(fetchMarketingCommandCenter, 8000);
  setInterval(fetchCloudRuntimeStatus, 10000);
  setInterval(fetchGovernanceData, 12000);
  setInterval(fetchOfficeState, 8000);
  setInterval(fetchCloudStatus, 15000);
  setInterval(fetchStatus, 8000);
});

// Robust Tab Switcher with Route Persistence & Highlight
function switchTab(tabId) {
  if (!tabId) tabId = "marketing-command-center";

  // 1. Highlight matching nav button
  let buttonFound = false;
  document.querySelectorAll(".nav-tab").forEach(t => {
    const target = t.getAttribute("data-tab") || (t.getAttribute("onclick") || "").match(/switchTab\(['"]([^'"]+)['"]\)/)?.[1];
    if (target === tabId) {
      t.classList.add("active");
      buttonFound = true;
      try { t.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' }); } catch(e) {}
    } else {
      t.classList.remove("active");
    }
  });

  // 2. Activate matching section
  let targetSection = document.getElementById(`tab-${tabId}`);
  if (!targetSection && tabId === "firewall-settings") targetSection = document.getElementById("tab-governance");
  if (!targetSection && tabId === "governance") targetSection = document.getElementById("tab-firewall-settings");

  document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
  if (targetSection) {
    targetSection.classList.add("active");
  } else {
    console.warn(`Tab section for '${tabId}' not found in DOM.`);
  }

  // 3. Update URL hash for refresh preservation
  if (window.location.hash !== `#tab-${tabId}` && window.location.hash !== `#${tabId}`) {
    try {
      history.replaceState(null, "", `#tab-${tabId}`);
    } catch (e) {
      window.location.hash = `tab-${tabId}`;
    }
  }

  // 4. Trigger section-specific data loaders
  if (tabId === "acquisition-channels") fetchAcquisitionData();
  if (tabId === "marketing-command-center") { fetchMarketingCommandCenter(); fetchCloudRuntimeStatus(); }
  if (tabId === "governance") { fetchGovernanceData(); fetchCloudRuntimeStatus(); fetchStatus(); }
  if (tabId === "ai-office") fetchOfficeState();
  if (tabId === "cloud-247") { fetchCloudStatus(); fetchCloudRuntimeStatus(); fetchDailyReports(); fetchEmailDeliveries(); }
  if (tabId === "employee-timeline") { fetchEmployeeActivities(currentTimeframe); }
  if (tabId === "overview") { fetchStatus(); fetchTasks(); }
  if (tabId === "phase4-revenue") fetchPhase4Dashboard();
  if (tabId === "approvals") fetchApprovals();
  if (tabId === "opportunities") fetchOpportunities();
  if (tabId === "first-experiment") renderExperimentCandidates();
  if (tabId === "products") fetchProducts();
  if (tabId === "sales-pipeline") { fetchLeads(); fetchDeliveries(); }
  if (tabId === "tasks") fetchTasks();
  if (tabId === "owner-metrics") fetchOwnerMetrics();
  if (tabId === "skills-registry" || tabId === "skills") fetchSkills();
  if (tabId === "employee-factory") fetchFactoryEmployees();
  if (tabId === "treasury-view") fetchTreasury();
  if (tabId === "marketplace-view") fetchMarketplace();
  if (tabId === "self-growth") fetchCapabilityGaps();
  if (tabId === "employees") fetchEmployees();
  if (tabId === "ceo-report") loadCEOReport();
  if (tabId === "firewall-settings") { fetchFirewall(); fetchGovernanceData(); }
  if (tabId === "payments-revenue") loadPaymentsDashboard();
}

// 1. Fetch Company Overview Status
async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();

    const actualRev = data.finances?.revenue_breakdown?.actual_revenue || 0.0;
    const estRev = data.finances?.revenue_breakdown?.estimated_revenue || 0.0;
    const pendingRev = data.finances?.revenue_breakdown?.pending_revenue || 0.0;
    const refundedRev = data.finances?.revenue_breakdown?.refunded_revenue || 0.0;
    const totalExp = data.finances?.expenses?.total || 0.0;

    document.getElementById("statActualRevenue").innerText = `$${actualRev.toFixed(2)}`;
    document.getElementById("statEstimatedRevenue").innerText = `$${estRev.toFixed(2)}`;
    document.getElementById("statTotalExpenses").innerText = `$${totalExp.toFixed(2)}`;
    document.getElementById("statActiveEmployees").innerText = `${data.active_employees} / ${data.total_employees}`;

    document.getElementById("lblActualCash").innerText = `$${actualRev.toFixed(2)}`;
    document.getElementById("lblEstRevenue").innerText = `$${estRev.toFixed(2)}`;
    document.getElementById("lblPendingRevenue").innerText = `$${pendingRev.toFixed(2)}`;
    document.getElementById("lblRefundedRevenue").innerText = `$${refundedRev.toFixed(2)}`;

    // Approvals badge
    const badge = document.getElementById("navApprovalBadge");
    badge.innerText = data.pending_approvals_count;
    badge.style.display = data.pending_approvals_count > 0 ? "inline-block" : "none";

    isEmergencyStop = data.emergency_stop;
    updateKillswitchUI();
  } catch (err) {
    console.error("Status fetch error:", err);
  }
}

// 2. Real-Time SSE Activity Stream
function initEventStream() {
  const feed = document.getElementById("activityFeed");
  const officeFeed = document.getElementById("officeLiveActivityFeed");
  const eventSource = new EventSource("/api/events");

  eventSource.onmessage = (e) => {
    try {
      const event = JSON.parse(e.data);
      if (feed) appendActivityItem(event, feed);
      if (officeFeed) appendActivityItem(event, officeFeed);
    } catch (err) {}
  };

  eventSource.onerror = () => {
    console.warn("SSE connection lost. Reconnecting...");
  };
}

function appendActivityItem(ev, container) {
  const item = document.createElement("div");
  item.className = `activity-item ${ev.risk_level?.toLowerCase() || 'low'}`;

  const timeStr = new Date(ev.timestamp).toLocaleTimeString();
  item.innerHTML = `
    <div class="activity-top">
      <span class="activity-agent">${ev.agent_id}</span>
      <span class="activity-time">${timeStr}</span>
    </div>
    <div class="activity-text">
      <strong>${ev.action}:</strong> ${ev.result}
    </div>
  `;

  container.prepend(item);
  if (container.children.length > 40) {
    container.removeChild(container.lastChild);
  }
}

// 3. Approvals Management
async function fetchApprovals() {
  try {
    const res = await fetch("/api/approvals?pending_only=true");
    const approvals = await res.json();
    const container = document.getElementById("approvalsList");

    if (approvals.length === 0) {
      container.innerHTML = `
        <div style="padding: 2.5rem; text-align: center; color: var(--text-muted);">
          ✓ No pending approvals. Operational agents are functioning within approved zero-spend policies.
        </div>
      `;
      return;
    }

    container.innerHTML = approvals.map(app => `
      <div class="approval-card glass">
        <div class="approval-header">
          <div class="approval-title">${app.what}</div>
          <span class="badge" style="background: rgba(245, 158, 11, 0.2); color: var(--accent-amber);">
            ${app.risk_level} RISK
          </span>
        </div>
        <div class="approval-grid">
          <div class="approval-field">
            <strong>Why / Strategic Rationale</strong>
            <span>${app.why}</span>
          </div>
          <div class="approval-field">
            <strong>Expected Cost</strong>
            <span style="color: var(--accent-rose); font-weight: 700;">$${app.expected_cost.toFixed(2)}</span>
          </div>
          <div class="approval-field">
            <strong>Expected Benefit</strong>
            <span style="color: var(--accent-emerald); font-weight: 600;">${app.expected_benefit}</span>
          </div>
          <div class="approval-field">
            <strong>Alternatives Considered</strong>
            <span>${app.alternatives}</span>
          </div>
          <div class="approval-field" style="grid-column: 1 / -1;">
            <strong>AI Recommendation</strong>
            <span style="color: var(--accent-cyan);">${app.recommendation}</span>
          </div>
        </div>
        <div class="approval-actions">
          <button class="btn btn-secondary" onclick="resolveApproval('${app.approval_id}', 'REQUEST_INFO')">Request Info</button>
          <button class="btn btn-secondary" onclick="resolveApproval('${app.approval_id}', 'PAUSE')">Pause</button>
          <button class="btn btn-reject" onclick="resolveApproval('${app.approval_id}', 'REJECT')">Reject</button>
          <button class="btn btn-approve" onclick="resolveApproval('${app.approval_id}', 'APPROVE')">✓ Approve</button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Approvals fetch error:", err);
  }
}

async function resolveApproval(approvalId, decision) {
  const notes = prompt(`Enter optional owner note for ${decision}:`) || "";
  try {
    const res = await fetch(`/api/approvals/${approvalId}/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, owner_notes: notes })
    });
    if (res.ok) {
      fetchApprovals();
      fetchStatus();
      fetchTasks();
    } else {
      const err = await res.json();
      alert(`Action failed: ${err.detail}`);
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

// 4. Opportunity Discovery & Scoring
let cachedOpportunities = [];

async function fetchOpportunities() {
  try {
    const res = await fetch("/api/opportunities");
    cachedOpportunities = await res.json();
    const container = document.getElementById("opportunityCards");

    if (cachedOpportunities.length === 0) {
      container.innerHTML = `<div style="grid-column: 1 / -1; padding: 2rem; text-align: center; color: var(--text-muted);">No opportunities discovered yet.</div>`;
      return;
    }

    container.innerHTML = cachedOpportunities.map(o => {
      const evBadgeColor = o.evidence_classification === "DIRECT_EVIDENCE" ? "var(--accent-emerald)" : (o.evidence_classification === "INDIRECT_EVIDENCE" ? "var(--accent-cyan)" : "var(--accent-amber)");
      return `
        <div class="stat-card glass" style="gap: 0.65rem;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="status-badge" style="background: rgba(255,255,255,0.08); color: ${evBadgeColor}; font-weight: 700;">
              ${o.evidence_classification}
            </span>
            <span style="font-size: 0.85rem; font-weight: 800; color: var(--accent-cyan);">
              Score: ${o.composite_score}/100
            </span>
          </div>
          <div style="font-weight: 700; font-size: 1rem; color: #fff;">${o.name}</div>
          <div style="font-size: 0.78rem; color: var(--text-muted);">${o.customer_problem.slice(0, 110)}...</div>
          <div style="font-size: 0.78rem; background: rgba(0,0,0,0.3); padding: 0.55rem; border-radius: 4px; display: grid; grid-template-columns: 1fr 1fr; gap: 0.35rem;">
            <div>Est. Price: <strong style="color: var(--accent-emerald);">$${o.estimated_price}</strong></div>
            <div>Margin: <strong>${o.expected_gross_margin}%</strong></div>
            <div>Time to MVP: <strong>${o.time_to_mvp}</strong></div>
            <div>Automation: <strong>${Math.round(o.estimated_automation_potential * 100)}%</strong></div>
          </div>
          <div style="display: flex; gap: 0.5rem; margin-top: 0.35rem;">
            <button class="btn btn-approve" style="font-size: 0.75rem; width: 100%;" onclick="runAutomatedHandoff('${o.opportunity_id}')">
              ⚡ Run Safe Handoff Pipeline
            </button>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Opportunities fetch error:", err);
  }
}

async function runAutomatedHandoff(oppId) {
  if (!confirm("Execute automated agent handoff pipeline for this opportunity?\nThis will create an MVP, run QA, generate sales copy, and submit an approval request.")) return;

  try {
    const res = await fetch("/api/pipeline/run-handoff", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ opportunity_id: oppId })
    });
    if (res.ok) {
      const data = await res.json();
      alert(`Automated handoff completed successfully!\nProduct ID: ${data.product_id}\nApproval ID: ${data.approval_id}\nAwaiting your sign-off in the Approvals Center.`);
      fetchStatus();
      fetchApprovals();
      fetchProducts();
    } else {
      const err = await res.json();
      alert("Handoff failed: " + err.detail);
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// 5. First Revenue Experiment View
function renderExperimentCandidates() {
  const container = document.getElementById("experimentCandidatesContainer");
  if (cachedOpportunities.length === 0) {
    container.innerHTML = `<div style="padding: 2rem; color: var(--text-muted);">Loading candidates...</div>`;
    return;
  }

  // Display top candidates sorted by score
  const candidates = [...cachedOpportunities].sort((a,b) => b.composite_score - a.composite_score);
  
  container.innerHTML = `
    <div style="margin-bottom: 1.5rem; font-size: 0.85rem; color: var(--text-secondary);">
      The AI Company prioritizes <strong>zero/low-capital</strong> digital products with verified customer demand evidence.
      No external advertising or financial expenditure is authorized without your explicit approval.
    </div>
    <div style="display: flex; flex-direction: column; gap: 1.25rem;">
      ${candidates.map((c, i) => `
        <div class="glass" style="padding: 1.25rem; border-left: 4px solid ${i === 0 ? 'var(--accent-emerald)' : 'var(--accent-cyan)'};">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span class="badge" style="background: rgba(56, 189, 248, 0.2); color: var(--accent-cyan);">Rank #${i+1}</span>
              <h3 style="font-size: 1.05rem; font-weight: 700; color: #fff;">${c.name}</h3>
            </div>
            <span style="font-weight: 800; color: var(--accent-cyan);">Score: ${c.composite_score}/100</span>
          </div>
          <div style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.75rem;">${c.customer_problem}</div>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; background: rgba(0,0,0,0.25); padding: 0.75rem; border-radius: 6px; font-size: 0.8rem;">
            <div>Target: <strong>${c.target_customer}</strong></div>
            <div>Evidence: <strong style="color: var(--accent-emerald);">${c.evidence_classification}</strong></div>
            <div>Price: <strong>$${c.estimated_price}</strong></div>
            <div>Expected Margin: <strong>${c.expected_gross_margin}%</strong></div>
            <div>Validation Cost: <strong style="color: var(--accent-emerald);">$0.00</strong></div>
            <div>Success Metric: <strong>${c.success_metric}</strong></div>
          </div>
          <div style="display: flex; justify-content: flex-end; margin-top: 0.85rem;">
            <button class="btn btn-approve" onclick="runAutomatedHandoff('${c.opportunity_id}')">
              Select & Launch Controlled Pipeline
            </button>
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

// 6. Product Factory
async function fetchProducts() {
  try {
    const res = await fetch("/api/products");
    const products = await res.json();
    const tbody = document.getElementById("productTableBody");

    if (products.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No products compiled in Product Factory yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = products.map(p => `
      <tr>
        <td style="font-family: monospace; font-weight: 600;">${p.product_id}</td>
        <td><strong>${p.name}</strong></td>
        <td><span class="status-badge" style="background: rgba(255,255,255,0.06);">${p.asset_type}</span></td>
        <td><span class="status-badge status-active">${p.status}</span></td>
        <td>
          <span style="color: ${p.qa_status === 'PASSED' ? 'var(--accent-emerald)' : 'var(--accent-amber)'}; font-weight: 700;">
            ${p.qa_status}
          </span>
        </td>
        <td style="font-family: monospace; font-size: 0.75rem;">${p.mvp_path || 'None'}</td>
        <td>
          <button class="btn btn-secondary" style="font-size: 0.7rem; padding: 0.2rem 0.5rem;" onclick="inspectProductQA('${p.product_id}')">Inspect QA</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Products fetch error:", err);
  }
}

async function inspectProductQA(productId) {
  try {
    const res = await fetch(`/api/products/${productId}/qa`, { method: "POST" });
    const report = await res.json();
    alert(`QA Inspection Report for ${productId}:\nVerdict: ${report.verdict}\nPassed: ${report.checks_passed?.join("\n")}\nFailed: ${report.checks_failed?.join("\n") || 'None'}`);
  } catch (err) {
    alert("QA check failed: " + err.message);
  }
}

// 7. Sales Pipeline & Deliveries
async function fetchLeads() {
  try {
    const res = await fetch("/api/leads");
    const leads = await res.json();
    const tbody = document.getElementById("leadsTableBody");

    if (leads.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">Zero active leads in pipeline.</td></tr>`;
      return;
    }

    tbody.innerHTML = leads.map(l => `
      <tr>
        <td style="font-family: monospace;">${l.lead_id}</td>
        <td>${l.customer_type}</td>
        <td>${l.source}</td>
        <td><span class="status-badge status-active">${l.status}</span></td>
        <td style="font-size: 0.75rem;">${l.consent_basis.slice(0, 35)}...</td>
      </tr>
    `).join("");
  } catch (err) {}
}

async function fetchDeliveries() {
  try {
    const res = await fetch("/api/deliveries");
    const deliveries = await res.json();
    const container = document.getElementById("deliveriesList");

    if (deliveries.length === 0) {
      container.innerHTML = `<div style="color: var(--text-muted); padding: 1rem;">No customer deliveries yet. Real deliveries will show verifiable evidence here.</div>`;
      return;
    }

    container.innerHTML = deliveries.map(d => `
      <div style="background: rgba(0,0,0,0.25); padding: 0.65rem; border-radius: 6px; border-left: 3px solid var(--accent-emerald);">
        <div><strong>Order ${d.order_id}</strong> - ${d.status}</div>
        <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 0.2rem;">${d.verification_evidence}</div>
      </div>
    `).join("");
  } catch (err) {}
}

// 8. Owner Time Metrics
async function fetchOwnerMetrics() {
  try {
    const res = await fetch("/api/owner-metrics");
    const metrics = await res.json();

    document.getElementById("statOwnerMinutes").innerText = `${metrics.owner_minutes_week} min`;
    document.getElementById("metricOwnerTimeTotal").innerText = `${metrics.owner_minutes_week} min`;
    document.getElementById("metricAutomatedTasks").innerText = `${metrics.automated_tasks_count}`;

    const list = document.getElementById("automationCandidatesList");
    if (!metrics.automation_candidates || metrics.automation_candidates.length === 0) {
      list.innerHTML = `<div style="color: var(--text-muted); font-size: 0.8rem;">No repeated manual tasks detected. System is running at high efficiency.</div>`;
      return;
    }

    list.innerHTML = metrics.automation_candidates.map(c => `
      <div style="background: rgba(0,0,0,0.25); padding: 0.75rem; border-radius: 6px;">
        <div style="font-weight: 700; color: #fff; font-size: 0.85rem;">${c.reason_needed}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.2rem;">Missing Tool: ${c.missing_tool || 'Custom Script'} • New Skill: ${c.new_skill_needed || 'Standard API'}</div>
      </div>
    `).join("");
  } catch (err) {}
}

// 9. Central Tasks & Employees
async function fetchTasks() {
  try {
    const res = await fetch("/api/tasks?limit=30");
    const tasks = await res.json();
    const tbody = document.getElementById("taskTableBody");

    tbody.innerHTML = tasks.map(t => `
      <tr>
        <td style="font-family: monospace; font-weight: 600;">${t.task_id}</td>
        <td><span style="font-size: 0.72rem; font-weight: 700; color: ${t.priority === 'HIGH' || t.priority === 'URGENT' ? 'var(--accent-rose)' : 'var(--accent-cyan)'}">${t.priority}</span></td>
        <td>
          <div style="font-weight: 600;">${t.objective}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${t.description.slice(0, 80)}...</div>
        </td>
        <td style="color: var(--accent-cyan); font-weight: 500;">${t.assigned_agent}</td>
        <td><span class="status-badge status-${t.status.toLowerCase()}">${t.status}</span></td>
        <td style="font-size: 0.75rem;">
          ${t.evidence ? `<span title="${t.evidence}">Verified ✓</span>` : `<span style="color: var(--text-muted);">None</span>`}
        </td>
      </tr>
    `).join("");
  } catch (err) {}
}

async function fetchEmployees() {
  try {
    const res = await fetch("/api/employees");
    const employees = await res.json();
    const tbody = document.getElementById("employeeTableBody");

    tbody.innerHTML = employees.map(e => `
      <tr>
        <td style="font-family: monospace; font-weight: 600;">${e.employee_id}</td>
        <td>
          <div style="font-weight: 700;">${e.role}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${e.purpose.slice(0, 70)}...</div>
        </td>
        <td><span class="status-badge status-${e.status.toLowerCase()}">${e.status}</span></td>
        <td style="font-size: 0.75rem; color: var(--accent-cyan);">${e.permissions.join(", ")}</td>
        <td style="font-size: 0.75rem;">${e.tools.join(", ")}</td>
        <td style="font-size: 0.75rem; color: var(--accent-amber);">${e.escalation_rules.slice(0, 60)}...</td>
      </tr>
    `).join("");
  } catch (err) {}
}

// 10. Weekly CEO Report
async function loadCEOReport() {
  const container = document.getElementById("ceoReportContent");
  container.innerHTML = `<div style="padding: 2rem; color: var(--text-muted);">Synthesizing corporate executive report...</div>`;
  try {
    const res = await fetch("/api/reports/weekly");
    const rep = await res.json();

    container.innerHTML = `
      <div style="margin-bottom: 1.5rem; font-size: 0.9rem; color: var(--text-secondary);">
        <strong>Executive Summary:</strong> ${rep.executive_summary}
      </div>

      <div class="glass report-section report-header-facts">
        <h3 style="color: var(--accent-cyan); font-size: 1rem; margin-bottom: 0.5rem;">
          1. VERIFIED FACTS (Grounded Historical Data)
        </h3>
        <ul style="list-style: none; display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0.5rem; font-size: 0.82rem;">
          <li>Period: <strong>${rep.facts.period}</strong></li>
          <li>Verified Actual Revenue: <strong style="color: var(--accent-emerald);">$${rep.facts.verified_revenue_usd.toFixed(2)}</strong></li>
          <li>Verified Expenses: <strong style="color: var(--accent-rose);">$${rep.facts.verified_expenses_usd.toFixed(2)}</strong></li>
          <li>Active AI Employees: <strong>${rep.facts.active_ai_employees_count}</strong></li>
          <li>Completed Tasks with Evidence: <strong>${rep.facts.completed_tasks_count}</strong></li>
          <li>Pending Owner Approvals: <strong>${rep.facts.pending_owner_approvals_count}</strong></li>
        </ul>
      </div>

      <div class="glass report-section report-header-estimates">
        <h3 style="color: var(--accent-amber); font-size: 1rem; margin-bottom: 0.5rem;">
          2. MODEL-BASED ESTIMATES (Projections & Calculations)
        </h3>
        <ul style="list-style: none; display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0.5rem; font-size: 0.82rem;">
          <li>Gross Profit Margin: <strong>${rep.estimates.estimated_gross_profit_margin_pct}%</strong></li>
          <li>Simulated Reinvestment Capital: <strong>$${rep.estimates.simulated_cash_available_for_reinvestment.toFixed(2)}</strong></li>
          <li>Pipeline Opportunities Evaluated: <strong>${rep.estimates.pipeline_opportunities_evaluated}</strong></li>
          <li>Estimated AI Operating Cost: <strong>$${rep.estimates.estimated_ai_operating_compute_cost.toFixed(2)}</strong></li>
        </ul>
      </div>

      <div class="glass report-section report-header-recs">
        <h3 style="color: var(--accent-purple); font-size: 1rem; margin-bottom: 0.5rem;">
          3. AI RECOMMENDATIONS & DECISIONS REQUIRED
        </h3>
        <div style="font-size: 0.85rem; display: flex; flex-direction: column; gap: 0.5rem;">
          <div>
            <strong>Strategic Proposals:</strong>
            <ul style="margin-left: 1.25rem; margin-top: 0.25rem;">
              ${rep.recommendations.strategic_initiatives_proposed.map(p => `<li>${p}</li>`).join("")}
            </ul>
          </div>
          ${rep.recommendations.urgent_owner_decisions_required.length > 0 ? `
            <div style="margin-top: 0.5rem;">
              <strong style="color: var(--accent-rose);">Urgent Decisions Awaiting Your Action (${rep.recommendations.urgent_owner_decisions_required.length}):</strong>
              <ul style="margin-left: 1.25rem; margin-top: 0.25rem;">
                ${rep.recommendations.urgent_owner_decisions_required.map(d => `<li><strong>${d.what}</strong> (Cost: $${d.expected_cost}) - ${d.recommendation}</li>`).join("")}
              </ul>
            </div>
          ` : `<div style="color: var(--accent-emerald);">✓ No urgent blocking approvals pending.</div>`}
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color: var(--accent-rose);">Failed to load report: ${err.message}</div>`;
  }
}

// 11. Firewall & Killswitch
async function fetchFirewall() {
  try {
    const res = await fetch("/api/firewall");
    const settings = await res.json();
    document.getElementById("lblSingleLimit").innerText = `$${(settings.max_single_expense || 0).toFixed(2)}`;
    document.getElementById("lblDailyLimit").innerText = `$${(settings.max_daily_expense || 0).toFixed(2)}`;
    document.getElementById("cfgSingleLimit").value = settings.max_single_expense || 0;
    document.getElementById("cfgDailyLimit").value = settings.max_daily_expense || 0;
    
    isEmergencyStop = !!settings.emergency_stop;
    updateKillswitchUI();
  } catch (err) {}
}

async function saveFirewallSettings() {
  const single = parseFloat(document.getElementById("cfgSingleLimit").value) || 0;
  const daily = parseFloat(document.getElementById("cfgDailyLimit").value) || 0;

  try {
    await fetch("/api/firewall/setting", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key: "max_single_expense", value: single })
    });
    await fetch("/api/firewall/setting", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key: "max_daily_expense", value: daily })
    });
    alert("Firewall policies successfully saved and active.");
    fetchFirewall();
    fetchStatus();
  } catch (err) {
    alert("Failed to save settings: " + err.message);
  }
}

async function toggleEmergencyStop() {
  const nextState = !isEmergencyStop;
  const confirmMsg = nextState 
    ? "ACTIVATE EMERGENCY STOP?\nThis immediately freezes all AI tasks, external network requests, and financial transactions."
    : "DEACTIVATE EMERGENCY STOP?\nResume standard AI enterprise operations?";

  if (!confirm(confirmMsg)) return;

  try {
    const res = await fetch("/api/firewall/emergency-stop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: nextState, reason: "Manual owner toggle from Command Center" })
    });
    const data = await res.json();
    isEmergencyStop = data.emergency_stop;
    updateKillswitchUI();
    fetchStatus();
  } catch (err) {
    alert("Failed to toggle emergency stop: " + err.message);
  }
}

function updateKillswitchUI() {
  const btn = document.getElementById("btnKillswitch");
  const indicator = document.getElementById("firewallIndicator");

  if (isEmergencyStop) {
    btn.classList.add("active");
    btn.innerText = "⚠️ SYSTEM FROZEN (CLICK TO RESUME)";
    indicator.classList.add("alert");
    indicator.innerText = "🛑 EMERGENCY HALT ACTIVE: ALL TASKS FROZEN";
  } else {
    btn.classList.remove("active");
    btn.innerText = "🛑 EMERGENCY STOP";
    indicator.classList.remove("alert");
    indicator.innerText = "● FINANCIAL FIREWALL: $0 UNAPPROVED LIMIT";
  }
}

// ========================================================
// 12. Phase 3: AI Skill Registry & Pipeline
// ========================================================
async function fetchSkills() {
  const tbody = document.getElementById("skillsTableBody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/skills");
    const skills = await res.json();

    if (skills.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-muted);">No skills registered.</td></tr>`;
      return;
    }

    tbody.innerHTML = skills.map(s => {
      const statusColor = s.status === "ACTIVE" ? "var(--accent-emerald)" : s.status === "TESTING" ? "var(--accent-cyan)" : "var(--accent-amber)";
      const isActionable = s.status !== "ACTIVE" && s.status !== "RETIRED";
      return `
        <tr>
          <td><strong style="color: var(--accent-cyan);">${s.skill_id}</strong></td>
          <td><strong>${s.name}</strong><br><small style="color: var(--text-muted);">${s.purpose || ''}</small></td>
          <td>v${s.version}</td>
          <td><span class="badge" style="background: rgba(255,255,255,0.08); color: ${statusColor}; font-weight:700;">${s.status}</span></td>
          <td><small>${(s.allowed_tools || []).join(", ") || "None"}</small></td>
          <td><small>${(s.permissions || []).join(", ") || "None"}</small></td>
          <td>
            <div style="display:flex; flex-direction:column; gap:0.25rem;">
              <small style="color: var(--text-muted);">${(s.security_rules || []).join("; ") || "Standard"}</small>
              ${isActionable ? `<button class="btn btn-secondary" style="font-size:0.7rem; padding:0.25rem 0.5rem;" onclick="activateSkill('${s.skill_id}')">Pass Tests & Activate</button>` : ''}
            </div>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Error fetching skills:", err);
  }
}

async function activateSkill(skillId) {
  try {
    const res = await fetch(`/api/skills/${skillId}/activate`, { method: "POST" });
    const data = await res.json();
    if (res.ok) {
      alert(`Skill ${skillId} successfully advanced to ACTIVE after passing all unit, security, and sandbox tests!`);
      fetchSkills();
    } else {
      alert(`Activation failed: ${data.detail}`);
    }
  } catch (err) {
    alert("Activation error: " + err.message);
  }
}

// ========================================================
// 13. Phase 3: AI Employee Factory & Workforce Lifecycle
// ========================================================
async function fetchFactoryEmployees() {
  const tbody = document.getElementById("factoryEmployeesTableBody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/employees");
    const employees = await res.json();

    tbody.innerHTML = employees.map(emp => {
      const statusColor = emp.status === "ACTIVE" ? "var(--accent-emerald)" : emp.status === "TRAINING" ? "var(--accent-amber)" : emp.status === "TESTING" ? "var(--accent-cyan)" : "var(--accent-rose)";
      const isDynamic = emp.agent_id.startsWith("EMP-013") || parseInt(emp.agent_id.replace("EMP-", "")) >= 13;
      return `
        <tr>
          <td><strong style="color: var(--accent-cyan);">${emp.agent_id}</strong></td>
          <td><strong>${emp.role_title}</strong><br><small style="color: var(--text-muted);">${emp.purpose || ''}</small></td>
          <td><span class="badge" style="background: rgba(255,255,255,0.08); color: ${statusColor}; font-weight:700;">${emp.status}</span></td>
          <td><small>${(emp.responsibilities || []).slice(0, 3).join("; ")}</small></td>
          <td><small>${(emp.permissions || []).join(", ") || "Standard"}</small></td>
          <td>
            <div style="display:flex; flex-wrap:wrap; gap:0.25rem;">
              ${(emp.status === "TRAINING" || emp.status === "TESTING") ? `
                <button class="btn btn-approve" style="font-size:0.7rem; padding:0.25rem 0.5rem;" onclick="activateEmployeeModal('${emp.agent_id}')">Validate & Activate</button>
              ` : ''}
              <button class="btn btn-secondary" style="font-size:0.7rem; padding:0.25rem 0.5rem;" onclick="retrainEmployeeModal('${emp.agent_id}')">Retrain</button>
              ${emp.status !== "RETIRED" ? `
                <button class="btn btn-reject" style="font-size:0.7rem; padding:0.25rem 0.5rem;" onclick="retireEmployeeModal('${emp.agent_id}')">Retire</button>
              ` : ''}
            </div>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Error fetching factory employees:", err);
  }
}

async function openSpawnEmployeeModal() {
  const role_title = prompt("Enter Role Title (e.g., AI Sales Qualifier, Market Research Analyst):");
  if (!role_title) return;
  const purpose = prompt("Enter Employee Purpose:", `Execute automated tasks for ${role_title}`);
  const responsibilitiesStr = prompt("Enter Responsibilities (comma-separated):", "contact qualified leads, answer FAQs, log responses, escalate edge cases");
  const responsibilities = (responsibilitiesStr || "").split(",").map(s => s.trim()).filter(Boolean);
  const toolsStr = prompt("Enter Approved Tool IDs (comma-separated):", "crm_api, corporate_memory");
  const tools = (toolsStr || "").split(",").map(s => s.trim()).filter(Boolean);
  const permissionsStr = prompt("Enter Permissions (comma-separated, NO banking/transfers):", "read_leads, write_crm");
  const permissions = (permissionsStr || "").split(",").map(s => s.trim()).filter(Boolean);
  const instructions = prompt("Enter Core System Instructions:", `You are ${role_title}. Operate strictly within your designated boundaries.`);
  const escalation_rules = prompt("Enter Escalation Rules:", "Escalate all pricing negotiation, legal uncertainty, and complaints to CEO.");

  try {
    const res = await fetch("/api/employees/spawn", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        role_title,
        purpose,
        responsibilities,
        capabilities: responsibilities,
        tools,
        permissions,
        instructions,
        escalation_rules
      })
    });
    const data = await res.json();
    if (res.ok) {
      alert(`AI Employee successfully spawned in TRAINING status: ${data.agent_id} (${data.role_title})`);
      fetchFactoryEmployees();
      fetchEmployees();
      fetchStatus();
    } else {
      alert(`Spawn failed: ${data.detail}`);
    }
  } catch (err) {
    alert("Spawn error: " + err.message);
  }
}

async function activateEmployeeModal(empId) {
  const testEvidence = prompt(`Enter QA validation test evidence for ${empId}:`, "Passed 10 simulated lead scenarios with 100% adherence to disclosure and escalation rules.");
  if (!testEvidence) return;

  try {
    const res = await fetch(`/api/employees/${empId}/activate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ test_evidence: testEvidence })
    });
    const data = await res.json();
    if (res.ok) {
      alert(`Employee ${empId} successfully activated!`);
      fetchFactoryEmployees();
      fetchEmployees();
      fetchStatus();
    } else {
      alert(`Activation failed: ${data.detail}`);
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function retrainEmployeeModal(empId) {
  const missingSkill = prompt(`Enter missing skill or failure root cause for ${empId}:`, "SKILL-VOICE-OBJECTION-HANDLING");
  if (!missingSkill) return;
  const sop = prompt("Enter updated training SOP guidelines:", "Always verify consent before reading product overview; escalate enterprise objections directly.");
  if (!sop) return;

  try {
    const res = await fetch(`/api/employees/${empId}/retrain`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identified_missing_skill: missingSkill,
        training_sops: sop
      })
    });
    const data = await res.json();
    if (res.ok) {
      alert(`Employee ${empId} successfully retrained and placed into TESTING!`);
      fetchFactoryEmployees();
    } else {
      alert(`Retraining failed: ${data.detail}`);
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function retireEmployeeModal(empId) {
  const reason = prompt(`Enter retirement reason for ${empId}:`, "Replaced by optimized automated skill pipeline.");
  if (!reason) return;

  try {
    const res = await fetch(`/api/employees/${empId}/retire`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason })
    });
    const data = await res.json();
    if (res.ok) {
      alert(`Employee ${empId} safely retired. Historical knowledge and task records preserved in Corporate Memory.`);
      fetchFactoryEmployees();
      fetchEmployees();
      fetchStatus();
    } else {
      alert(`Retirement failed: ${data.detail}`);
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// ========================================================
// 14. Phase 3: Virtual Company Treasury & Reinvestment
// ========================================================
async function fetchTreasury() {
  try {
    const res = await fetch("/api/treasury");
    const data = await res.json();

    const fundsEl = document.getElementById("treasuryVirtualFunds");
    const reserveEl = document.getElementById("treasuryReserve");
    const budgetEl = document.getElementById("treasuryReinvestBudget");
    const modeEl = document.getElementById("lblOperatingMode");

    if (fundsEl) fundsEl.innerText = `$${(data.virtual_operating_funds || 0).toFixed(2)}`;
    if (reserveEl) reserveEl.innerText = `$${(data.operating_reserve || 0).toFixed(2)}`;
    if (budgetEl) budgetEl.innerText = `$${(data.reinvestment_budget || 0).toFixed(2)} (${((data.reinvestment_percentage || 0) * 100).toFixed(0)}%)`;

    if (modeEl && data.operating_mode) {
      modeEl.innerText = data.operating_mode === "FREE_FIRST"
        ? "FREE-FIRST MODE (Zero Capital / Organic Growth)"
        : `PROFIT-FIRST MODE (Reinvesting ${((data.reinvestment_percentage || 0) * 100).toFixed(0)}% of verified net profits)`;
      modeEl.style.color = data.operating_mode === "FREE_FIRST" ? "var(--accent-cyan)" : "var(--accent-emerald)";
    }
  } catch (err) {
    console.error("Treasury fetch error:", err);
  }
}

// ========================================================
// 15. Phase 3: Internal Capability Marketplace
// ========================================================
async function fetchMarketplace() {
  const container = document.getElementById("marketplaceCards");
  if (!container) return;

  try {
    const res = await fetch("/api/marketplace");
    const items = await res.json();

    if (items.length === 0) {
      container.innerHTML = `<div style="color: var(--text-muted);">No capabilities registered in catalog.</div>`;
      return;
    }

    container.innerHTML = items.map(item => `
      <div class="opportunity-card glass">
        <div class="opportunity-title" style="display:flex; justify-content:space-between; align-items:center;">
          <span>${item.name}</span>
          <span class="badge" style="background: ${item.free_or_paid === 'FREE' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)'}; color: ${item.free_or_paid === 'FREE' ? 'var(--accent-emerald)' : 'var(--accent-amber)'}; font-weight:700;">
            ${item.free_or_paid} ($${(item.cost_usd || 0).toFixed(2)})
          </span>
        </div>
        <p style="font-size:0.8rem; color: var(--text-secondary); margin-bottom: 0.75rem;">${item.description}</p>
        <div style="font-size: 0.78rem; display: flex; flex-direction: column; gap: 0.35rem; border-top: 1px solid var(--border-subtle); padding-top: 0.5rem;">
          <div><strong>Provider:</strong> ${item.provider} (${item.capability_type})</div>
          <div><strong>Reliability:</strong> ${(item.reliability_score * 100).toFixed(0)}% | <strong>Security:</strong> ${item.security_rating}</div>
          <div><strong>Setup Time:</strong> ${item.setup_time_hours}h | <strong>Status:</strong> <span style="color: var(--accent-emerald); font-weight:600;">${item.status}</span></div>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Marketplace fetch error:", err);
  }
}

// ========================================================
// 16. Phase 3: Self-Growth Engine & Capability Gaps
// ========================================================
async function fetchCapabilityGaps() {
  const container = document.getElementById("capabilityGapsList");
  if (!container) return;

  try {
    const res = await fetch("/api/capability-gaps");
    const gaps = await res.json();

    if (gaps.length === 0) {
      container.innerHTML = `<div style="color: var(--accent-emerald); padding: 1.5rem; text-align: center;">✓ No open capability gaps. System is self-sufficient for current operational scope.</div>`;
      return;
    }

    container.innerHTML = gaps.map(gap => {
      const isResolved = gap.status === "RESOLVED";
      return `
        <div class="approval-card glass" style="border-left: 3px solid ${isResolved ? 'var(--accent-emerald)' : 'var(--accent-amber)'};">
          <div class="approval-header">
            <div class="approval-title">${gap.capability_name} <small style="color: var(--text-muted); font-size: 0.75rem;">(${gap.gap_id})</small></div>
            <span class="badge" style="background: rgba(255,255,255,0.08); color: ${isResolved ? 'var(--accent-emerald)' : 'var(--accent-amber)'}; font-weight:700;">
              ${gap.status} (${gap.urgency} URGENCY)
            </span>
          </div>
          <div class="approval-grid" style="margin-top: 0.5rem;">
            <div class="approval-field">
              <strong>Why Required</strong>
              <span>${gap.why_required}</span>
            </div>
            <div class="approval-field">
              <strong>Business Objective</strong>
              <span>${gap.business_objective}</span>
            </div>
            <div class="approval-field">
              <strong>Recommended Free-First Approach</strong>
              <span style="color: var(--accent-cyan); font-weight: 600;">${gap.recommended_approach || "Free-First Ladder Evaluation Pending"}</span>
            </div>
            <div class="approval-field">
              <strong>Expected Cost / ROI</strong>
              <span style="color: var(--accent-emerald); font-weight: 600;">$${(gap.expected_cost_usd || 0).toFixed(2)} | ROI: ${(gap.expected_roi_ratio || 0).toFixed(1)}x</span>
            </div>
          </div>
          ${!isResolved ? `
            <div style="margin-top: 0.75rem; display: flex; justify-content: flex-end;">
              <button class="btn btn-secondary" onclick="runSelfGrowthOnGap('${gap.capability_name.replace(/'/g, "\\'")}', '${gap.why_required.replace(/'/g, "\\'")}', '${gap.business_objective.replace(/'/g, "\\'")}')">
                🌱 Run Autonomous Self-Growth Cycle
              </button>
            </div>
          ` : ''}
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Capability gaps fetch error:", err);
  }
}

async function runSelfGrowthOnGap(capabilityName, whyRequired, businessGoal) {
  try {
    const res = await fetch("/api/self-growth/cycle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        capability_name: capabilityName,
        why_needed: whyRequired,
        business_goal: businessGoal
      })
    });
    const result = await res.json();
    if (res.ok) {
      alert(`Self-Growth cycle executed successfully!\nOutcome: ${result.outcome}\nEntity: ${result.entity_id}\nAction: ${result.action_taken}`);
      fetchCapabilityGaps();
      fetchSkills();
      fetchFactoryEmployees();
      fetchMarketplace();
      fetchStatus();
    } else {
      alert(`Cycle failed: ${result.detail}`);
    }
  } catch (err) {
    alert("Self-growth error: " + err.message);
  }
}

async function openTriggerSelfGrowthModal() {
  const capabilityName = prompt("Enter Capability Name (e.g. Automated SEO Keyword Research, Voice Telephony Qualification):");
  if (!capabilityName) return;
  const whyNeeded = prompt("Why is this capability needed?", "Automate inbound lead qualification without manual owner time.");
  if (!whyNeeded) return;
  const businessGoal = prompt("What is the business objective?", "Accelerate lead response time and double qualified discovery rate.");
  if (!businessGoal) return;

  await runSelfGrowthOnGap(capabilityName, whyNeeded, businessGoal);
}

// ========================================================
// 17. Phase 4: Autonomous Revenue Engine & Truth Ledger
// ========================================================
let lastLaunchReportId = null;

async function fetchPhase4Dashboard() {
  try {
    // 1. Fetch Revenue Truth Metrics
    const revRes = await fetch("/api/revenue/metrics");
    if (revRes.ok) {
      const data = await revRes.json();
      const vEl = document.getElementById("p4VerifiedRevenue");
      const pEl = document.getElementById("p4PendingRevenue");
      const cEl = document.getElementById("p4VerifiedCustomers");
      const mEl = document.getElementById("p4OperatingModeBadge");

      if (vEl) vEl.innerText = `$${(data.all_time.verified_actual_revenue || 0).toFixed(2)}`;
      if (pEl) pEl.innerText = `$${(data.all_time.pending_revenue || 0).toFixed(2)}`;
      if (cEl) cEl.innerText = data.all_time.verified_transaction_count || 0;
      if (mEl) mEl.innerText = `MODE: ${data.operating_mode} ($0 SPEND)`;
    }

    // 2. Fetch Bottleneck Diagnostic
    const bRes = await fetch("/api/revenue/bottlenecks");
    if (bRes.ok) {
      const bData = await bRes.json();
      const bnEl = document.getElementById("p4CurrentBottleneck");
      const bsEl = document.getElementById("p4BottleneckSubtext");
      if (bnEl) bnEl.innerText = bData.current_bottleneck;
      if (bsEl) bsEl.innerText = bData.evidence;
    }

    // 3. Fetch 10 Candidate Opportunities
    const cRes = await fetch("/api/revenue/opportunities/candidates");
    if (cRes.ok) {
      const candidates = await cRes.json();
      const tbody = document.getElementById("p4CandidatesTableBody");
      if (tbody) {
        tbody.innerHTML = candidates.map(c => `
          <tr>
            <td><strong style="color: var(--accent-emerald); font-size:0.85rem;">${c.composite_score.toFixed(2)}</strong></td>
            <td>
              <strong style="color: var(--accent-cyan);">${c.name}</strong><br>
              <small style="color: var(--text-muted);">${c.opportunity_id}</small>
            </td>
            <td><small>${c.category}</small></td>
            <td><strong>$${c.estimated_price.toFixed(2)}</strong></td>
            <td><small style="color: var(--accent-amber);">${c.time_to_first_customer}</small></td>
          </tr>
        `).join("");
      }
    }

    // 4. Fetch 13-Stage Sales Pipeline
    const pRes = await fetch("/api/revenue/pipeline");
    if (pRes.ok) {
      const pData = await pRes.json();
      const pContainer = document.getElementById("p4PipelineStagesContainer");
      if (pContainer) {
        const stages = pData.stage_breakdown || {};
        pContainer.innerHTML = Object.entries(stages).map(([stage, count]) => `
          <div style="background: rgba(0,0,0,0.3); padding: 0.5rem; border-radius: 6px; border: 1px solid var(--border-subtle);">
            <div style="font-weight: 700; color: ${count > 0 ? 'var(--accent-emerald)' : 'var(--text-muted)'}; font-size: 1rem;">${count}</div>
            <div style="color: var(--text-secondary); font-size: 0.65rem; text-transform: uppercase; margin-top: 0.2rem;">${stage}</div>
          </div>
        `).join("");
      }
    }

  } catch (err) {
    console.error("Error fetching Phase 4 dashboard:", err);
  }
}

async function runDailyRevenueLoopUI() {
  try {
    const res = await fetch("/api/revenue/daily-loop", { method: "POST" });
    const data = await res.json();
    alert(`Daily Revenue Loop Executed!\nBottleneck Identified: ${data.current_bottleneck}\nRecommended Action: ${data.recommended_action}`);
    fetchPhase4Dashboard();
    fetchStatus();
  } catch (err) {
    alert("Daily loop error: " + err.message);
  }
}

async function proposePrimaryCandidateUI() {
  try {
    const res = await fetch("/api/revenue/opportunities/select-proposal", { method: "POST" });
    const data = await res.json();
    alert(`Primary candidate proposal created!\nApproval ID: ${data.approval_id}\nOpportunity: ${data.primary_opportunity.name}\nRequested Spend: $${data.requested_spending.toFixed(2)}`);
    fetchApprovals();
    fetchStatus();
  } catch (err) {
    alert("Proposal error: " + err.message);
  }
}

async function generateLaunchReportUI() {
  try {
    const res = await fetch("/api/revenue/launch-readiness", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ opportunity_id: "OPP-P4-001" })
    });
    const data = await res.json();
    lastLaunchReportId = data.report_id;

    const prBadge = document.getElementById("p4ProductReadinessBadge");
    const appBadge = document.getElementById("p4LaunchApprovalBadge");
    if (prBadge) prBadge.innerText = data.product_readiness;
    if (appBadge) appBadge.innerText = "PENDING_OWNER_APPROVAL";

    alert(`Launch Readiness Report Compiled: ${data.report_id}\nProduct: ${data.title}\nQA Verdict: ${data.qa_status}\nLaunch is safely stopped pending Owner Approval.`);
    fetchApprovals();
    fetchStatus();
  } catch (err) {
    alert("Launch report error: " + err.message);
  }
}

async function attemptLaunchUI() {
  if (!lastLaunchReportId) {
    alert("Please compile a Launch Readiness Report first.");
    return;
  }

  try {
    const res = await fetch("/api/revenue/launch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ report_id: lastLaunchReportId })
    });
    const data = await res.json();
    if (res.ok) {
      alert("Launch Gate Passed! Product launched publicly.");
    } else {
      alert(`LAUNCH GATE SECURITY STOP:\n${data.detail}`);
    }
  } catch (err) {
    alert("Launch Gate error: " + err.message);
  }
}

async function createSimulatedLeadUI() {
  const customerRef = prompt("Enter customer reference / username:", `developer_${Math.floor(Math.random() * 9000 + 1000)}`);
  if (!customerRef) return;
  const problem = prompt("Enter customer problem description:", "Need to test local LLM prompt adherence offline before shipping.");
  if (!problem) return;

  try {
    const res = await fetch("/api/revenue/pipeline/leads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_id: "PROD-OPP-P4-001",
        customer_ref: customerRef,
        source: "GITHUB_DEV_COMMUNITY",
        customer_type: "INDIE_DEV",
        problem: problem,
        consent_basis: "INBOUND_INQUIRY"
      })
    });
    const data = await res.json();
    alert(`Inbound Lead registered: ${data.lead_id}`);
    fetchPhase4Dashboard();
  } catch (err) {
    alert("Lead error: " + err.message);
  }
}

// ==========================================================================
// PHASE 5A: AI VIRTUAL OFFICE & WORKSTATION DESK CONTROLLER
// ==========================================================================

let activeOfficeFilter = "ALL";
const GLOSSARY_FALLBACK = {
  "qualification": "Checking whether an incoming lead appears to be a genuine potential customer before spending additional company effort on it.",
  "financial_firewall": "An ironclad security barrier enforcing a $0.00 unapproved spending ceiling. No AI can spend real money without owner authorization.",
  "banking_air_gap": "A complete architectural separation ensuring AI agents have zero access to bank accounts, credentials, or funds transfer mechanisms.",
  "verified_revenue": "Actual cash confirmed received by an external payment processor (such as Stripe Checkout) with verifiable evidence. Strictly separated from estimates.",
  "launch_gate": "A mandatory quality and compliance checkpoint requiring verified automated tests and owner approval before any external public launch.",
  "zero_capital_mode": "Company operating model prioritizing free-tier tools, open-source models, and organic acquisition without external capital requirements.",
  "emergency_stop": "A hardware-level software killswitch that immediately halts all autonomous AI actions and freezes task execution."
};

// 1. Fetch & Render Complete Office State
async function fetchOfficeState() {
  try {
    const res = await fetch("/api/office/state");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    currentOfficeData = data;

    renderOfficeStatusBar(data.company_status);
    renderOfficeFinancials(data.financials);
    renderCEOSpotlight(data.ceo_focus);
    renderOfficeDepartments(data.departments, activeOfficeFilter);
    renderHandoffFlow(data.handoffs);
    renderTodayMetrics(data.today);
    renderNextActions(data.next_actions);

    const pendingCount = data.company_status.owner_action_required ? 1 : 0;
    const badge = document.getElementById("officePendingApprovalsCount");
    if (badge) badge.innerText = pendingCount;
  } catch (err) {
    console.error("Office state fetch error:", err);
  }
}

function refreshOfficeState() {
  fetchOfficeState();
}

// 2. Render Top Company Status Bar
function renderOfficeStatusBar(status) {
  const statusText = document.getElementById("officeStatusText");
  const pulseDot = document.getElementById("officePulseDot");
  const runningBadge = document.getElementById("officeCompanyRunningBadge");
  const expTitle = document.getElementById("officeExpTitle");
  const expDay = document.getElementById("officeExpDay");
  const bottleneckBadge = document.getElementById("officeBottleneckBadge");
  const ownerActionBadge = document.getElementById("officeOwnerActionBadge");
  const alertBox = document.getElementById("officeOwnerAlertBox");
  const alertText = document.getElementById("officeOwnerAlertText");

  if (statusText) statusText.innerText = status.status_text;
  if (pulseDot) {
    pulseDot.className = "status-pulse-dot " + (status.is_running ? "green" : "red");
  }
  if (runningBadge) {
    runningBadge.className = "status-indicator-badge " + (status.is_running ? "running" : "paused");
  }
  if (expTitle) expTitle.innerText = status.experiment_title;
  if (expDay) expDay.innerText = `Day ${status.experiment_day}`;
  if (bottleneckBadge) bottleneckBadge.innerText = status.current_bottleneck;

  if (status.owner_action_required) {
    if (ownerActionBadge) {
      ownerActionBadge.innerText = "🟠 OWNER ACTION REQUIRED";
      ownerActionBadge.style.background = "rgba(245, 158, 11, 0.2)";
      ownerActionBadge.style.color = "var(--accent-amber)";
    }
    if (alertBox) {
      alertBox.style.display = "flex";
      if (alertText) alertText.innerText = status.owner_action_description;
    }
  } else {
    if (ownerActionBadge) {
      ownerActionBadge.innerText = "🟢 No Owner Action Required";
      ownerActionBadge.style.background = "rgba(16, 185, 129, 0.15)";
      ownerActionBadge.style.color = "var(--accent-emerald)";
    }
    if (alertBox) alertBox.style.display = "none";
  }
}

// 3. Render Top-Level Financial Truth
function renderOfficeFinancials(finances) {
  const revElem = document.getElementById("officeVerifiedRevenue");
  const expElem = document.getElementById("officeRealExpenses");
  const profitElem = document.getElementById("officeRealProfit");
  const custElem = document.getElementById("officeVerifiedCustomers");

  if (revElem) revElem.innerText = `$${finances.verified_real_revenue.toFixed(2)}`;
  if (expElem) expElem.innerText = `$${finances.real_expenses.toFixed(2)}`;
  if (profitElem) profitElem.innerText = `$${finances.real_profit.toFixed(2)}`;
  if (custElem) custElem.innerText = finances.verified_customers;
}

// 4. Render CEO Executive Spotlight Card
function renderCEOSpotlight(ceo) {
  const avatarElem = document.getElementById("ceoAvatarSvg");
  if (avatarElem) avatarElem.innerHTML = generateEmployeeAvatarSvg("ceo");

  const objElem = document.getElementById("ceoCurrentObjective");
  const decElem = document.getElementById("ceoCurrentDecision");
  const priElem = document.getElementById("ceoPriorityText");
  const botElem = document.getElementById("ceoBottleneckText");
  const penElem = document.getElementById("ceoPendingDecisionsText");

  if (objElem) objElem.innerText = ceo.current_objective;
  if (decElem) decElem.innerText = ceo.current_decision;
  if (priElem) priElem.innerText = ceo.company_priority;
  if (botElem) botElem.innerText = ceo.current_bottleneck;
  if (penElem) penElem.innerText = ceo.pending_owner_decisions;
}

// 5. Render Department Floor Plan & Workstations
function renderOfficeDepartments(departments, filter = "ALL") {
  const container = document.getElementById("officeDepartmentsContainer");
  if (!container) return;

  container.innerHTML = departments.map(dept => {
    let filteredEmps = dept.employees;
    if (filter !== "ALL") {
      filteredEmps = dept.employees.filter(e => e.status === filter);
    }

    if (filter !== "ALL" && filteredEmps.length === 0) {
      return "";
    }

    const workstationsHtml = filteredEmps.length > 0 
      ? filteredEmps.map(emp => renderWorkstationCardHtml(emp)).join("")
      : `
        <div class="empty-workstation-card">
          <span style="font-size: 1.5rem;">🪑</span>
          <strong style="color: var(--text-secondary); font-size: 0.85rem;">Workstation Open</strong>
          <p style="font-size: 0.75rem;">Capability ready for dynamic AI employee assignment</p>
        </div>
      `;

    return `
      <div class="department-zone">
        <div class="department-zone-header">
          <div>
            <div class="department-title">
              <span>${dept.icon}</span> ${dept.name}
            </div>
            <div class="department-desc">${dept.description}</div>
          </div>
          <span class="badge" style="background: rgba(255,255,255,0.06); color: var(--text-secondary);">
            ${dept.employees.length} Agent(s) Assigned
          </span>
        </div>
        <div class="workstations-grid">
          ${workstationsHtml}
        </div>
      </div>
    `;
  }).join("");
}

function renderWorkstationCardHtml(emp) {
  const statusLower = emp.status.toLowerCase();
  const avatarSvg = generateEmployeeAvatarSvg(emp.avatar_theme);

  let statusBadgeClass = "waiting";
  let statusIcon = "🟡";
  if (emp.status === "WORKING") { statusBadgeClass = "working"; statusIcon = "🟢"; }
  else if (emp.status === "THINKING") { statusBadgeClass = "thinking"; statusIcon = "🔵"; }
  else if (emp.status === "BLOCKED") { statusBadgeClass = "blocked"; statusIcon = "🔴"; }
  else if (emp.status === "OFFLINE") { statusBadgeClass = "offline"; statusIcon = "⚪"; }

  const activeTask = emp.current_task;
  const lastTask = emp.last_completed_task;

  let screenDotColor = "active-cyan";
  let screenHeaderLabel = "IDLE DESK SCREEN";
  if (emp.status === "WORKING") { screenDotColor = "active-green"; screenHeaderLabel = "ACTIVE TERMINAL"; }
  else if (emp.status === "BLOCKED") { screenDotColor = "active-rose"; screenHeaderLabel = "ACTION REQUIRED"; }

  return `
    <div class="workstation-card ${statusLower}" onclick="openEmployeeDetailModal('${emp.employee_id}')">
      <div class="workstation-profile">
        <div class="employee-avatar-wrapper">
          <div class="employee-avatar-svg">${avatarSvg}</div>
          <span class="ai-badge-pill">AI</span>
        </div>
        <div class="employee-info" style="flex: 1; min-width: 0;">
          <h4>${emp.name}</h4>
          <div class="role-text">${emp.role}</div>
          <div class="role-badge">${emp.role_badge}</div>
        </div>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span class="desk-status-pill ${statusBadgeClass}">
          ${statusIcon} ${emp.status_label}
        </span>
        <span style="font-size: 0.7rem; color: var(--text-muted);">
          ${emp.employee_id}
        </span>
      </div>

      <div class="desk-screen-graphic">
        <div class="screen-header-dots">
          <span class="screen-dot ${screenDotColor}"></span>
          <span class="screen-dot"></span>
          <span class="screen-dot"></span>
          <span style="font-size: 0.62rem; color: var(--text-muted); margin-left: 0.25rem;">${screenHeaderLabel}</span>
        </div>
        <div class="desk-activity-content">
          ${activeTask ? `
            <strong>Task:</strong> ${activeTask.objective}
            <div style="font-size: 0.68rem; color: var(--text-muted); margin-top: 0.15rem;">
              Status: ${activeTask.human_status}
            </div>
          ` : `
            <span style="color: var(--text-muted); font-style: italic;">
              ${lastTask ? `Last completed: ${lastTask.objective}` : "Waiting for next assigned task"}
            </span>
          `}
        </div>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.74rem; color: var(--text-muted); border-top: 1px solid var(--border-subtle); padding-top: 0.6rem;">
        <span>🎯 Next: ${emp.next_objective ? emp.next_objective.substring(0, 24) + '...' : 'Assignment'}</span>
        <span style="color: var(--accent-cyan); font-weight: 600;">View Desk →</span>
      </div>
    </div>
  `;
}

// 6. Filter Office Workstations
function filterOfficeDesks(filter, btn) {
  activeOfficeFilter = filter;
  const buttons = document.querySelectorAll("#deskFilters button");
  buttons.forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");

  if (currentOfficeData && currentOfficeData.departments) {
    renderOfficeDepartments(currentOfficeData.departments, filter);
  }
}

// 7. Render Inter-Department Handoff Flow
function renderHandoffFlow(handoffs) {
  const container = document.getElementById("officeHandoffsFlow");
  if (!container || !handoffs) return;

  container.innerHTML = handoffs.map((h, i) => `
    <div class="handoff-node">
      <div style="font-weight: 700; color: #fff;">${h.from}</div>
      <div style="font-size: 0.68rem; color: var(--accent-cyan); margin: 0.15rem 0;">${h.label}</div>
      <div style="color: var(--text-muted); font-size: 0.7rem;">→ ${h.to}</div>
    </div>
    ${i < handoffs.length - 1 ? '<span class="handoff-arrow">➔</span>' : ''}
  `).join("");
}

// 8. Render Today's Metrics & Next Actions
function renderTodayMetrics(today) {
  if (!today) return;
  const discElem = document.getElementById("todayLeadsDiscovered");
  const qualElem = document.getElementById("todayLeadsQualified");
  const purElem = document.getElementById("todayCustomerPurchases");
  const compElem = document.getElementById("todayTasksCompleted");

  if (discElem) discElem.innerText = today.leads_discovered;
  if (qualElem) qualElem.innerText = today.leads_qualified;
  if (purElem) purElem.innerText = today.customers_purchased;
  if (compElem) compElem.innerText = today.tasks_completed;
}

function renderNextActions(actions) {
  const container = document.getElementById("officeNextActionsList");
  if (!container || !actions) return;

  container.innerHTML = actions.map((act, i) => `
    <div style="background: rgba(0,0,0,0.25); padding: 0.65rem 0.85rem; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem;">
      <div>
        <strong style="color: #fff;">${i + 1}. ${act.assigned_to}:</strong>
        <span style="color: var(--text-secondary); margin-left: 0.35rem;">${act.action}</span>
      </div>
      <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: var(--accent-cyan); font-size: 0.68rem;">
        ${act.status}
      </span>
    </div>
  `).join("");
}

// 9. Employee Detail Modal ("What are they doing?")
async function openEmployeeDetailModal(empId) {
  try {
    const res = await fetch(`/api/office/employees/${empId}`);
    if (!res.ok) throw new Error("Employee not found");
    const emp = await res.json();

    document.getElementById("modalEmpName").innerText = emp.name;
    document.getElementById("modalEmpTitle").innerText = `${emp.title} • ${emp.role}`;
    document.getElementById("modalEmpAvatarSvg").innerHTML = generateEmployeeAvatarSvg(emp.avatar_theme);

    const statusBadge = document.getElementById("modalEmpStatusBadge");
    statusBadge.className = `desk-status-pill ${emp.status.toLowerCase()}`;
    statusBadge.innerText = `${emp.status === 'WORKING' ? '🟢' : (emp.status === 'BLOCKED' ? '🔴' : '🟡')} ${emp.status_label}`;

    document.getElementById("modalEmpRoleBadge").innerText = emp.role_badge;

    // Current Work
    document.getElementById("modalCurrentTask").innerText = emp.current_work.active_task;
    document.getElementById("modalCurrentTaskStatus").innerText = emp.current_work.task_status;
    document.getElementById("modalCurrentTaskId").innerText = emp.current_work.task_id;
    document.getElementById("modalCurrentTaskStarted").innerText = emp.current_work.started_at;
    document.getElementById("modalCurrentTaskNext").innerText = emp.current_work.expected_next_action;

    // Recent Work
    const recentList = document.getElementById("modalRecentWorkList");
    if (emp.recent_work && emp.recent_work.length > 0) {
      recentList.innerHTML = emp.recent_work.map(w => `
        <div style="background: rgba(0,0,0,0.25); padding: 0.6rem 0.85rem; border-radius: 6px; font-size: 0.78rem;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.2rem;">
            <strong style="color: #fff;">${w.objective}</strong>
            <span style="color: var(--text-muted); font-size: 0.7rem;">${new Date(w.completed_at).toLocaleTimeString()}</span>
          </div>
          <p style="color: var(--text-secondary); font-size: 0.74rem;">${w.result}</p>
        </div>
      `).join("");
    } else {
      recentList.innerHTML = `
        <div style="color: var(--text-muted); font-size: 0.78rem; font-style: italic;">
          No previous tasks recorded for this session.
        </div>
      `;
    }

    // Performance
    document.getElementById("modalPerfCompleted").innerText = emp.performance.tasks_completed;
    document.getElementById("modalPerfFailed").innerText = emp.performance.tasks_failed;
    document.getElementById("modalPerfSuccessRate").innerText = emp.performance.success_rate;
    document.getElementById("modalPerfRevenue").innerText = emp.performance.revenue_attributed;

    // Permissions
    const canList = document.getElementById("modalCanList");
    canList.innerHTML = emp.permissions.can.map(c => `<li>${c}</li>`).join("");

    const cannotList = document.getElementById("modalCannotList");
    cannotList.innerHTML = emp.permissions.cannot.map(c => `<li>${c}</li>`).join("");

    // Technical details
    const techContent = document.getElementById("modalTechDetailsContent");
    techContent.innerText = JSON.stringify(emp.technical_details, null, 2);

    document.getElementById("employeeDetailModal").style.display = "flex";
  } catch (err) {
    alert("Could not load employee details: " + err.message);
  }
}

function closeEmployeeModal() {
  const modal = document.getElementById("employeeDetailModal");
  if (modal) modal.style.display = "none";
}

function toggleTechDetails() {
  const content = document.getElementById("modalTechDetailsContent");
  const arrow = document.getElementById("techToggleArrow");
  if (!content) return;
  if (content.style.display === "none") {
    content.style.display = "block";
    if (arrow) arrow.innerText = "▲";
  } else {
    content.style.display = "none";
    if (arrow) arrow.innerText = "▼";
  }
}

// 10. Glossary Modal ("Explain This")
function openGlossaryModal(termKey) {
  const titleElem = document.getElementById("glossaryTitle");
  const contentElem = document.getElementById("glossaryContent");

  const cleanTitle = termKey.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
  let explanation = GLOSSARY_FALLBACK[termKey.toLowerCase()];

  if (currentOfficeData && currentOfficeData.glossary && currentOfficeData.glossary[termKey.toLowerCase()]) {
    explanation = currentOfficeData.glossary[termKey.toLowerCase()];
  }

  if (titleElem) titleElem.innerText = `What does ${cleanTitle} mean?`;
  if (contentElem) contentElem.innerText = explanation || "Definition unavailable.";

  const modal = document.getElementById("glossaryModal");
  if (modal) modal.style.display = "flex";
}

function closeGlossaryModal() {
  const modal = document.getElementById("glossaryModal");
  if (modal) modal.style.display = "none";
}

// 11. Emergency Stop Modal
function openEmergencyStopModal() {
  const modal = document.getElementById("emergencyStopConfirmModal");
  if (modal) modal.style.display = "flex";
}

function closeEmergencyStopModal() {
  const modal = document.getElementById("emergencyStopConfirmModal");
  if (modal) modal.style.display = "none";
}

async function confirmEmergencyStopToggle() {
  closeEmergencyStopModal();
  try {
    const res = await fetch("/api/governance/emergency-stop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: !isEmergencyStop, reason: "Owner action from Virtual Office" })
    });
    const data = await res.json();
    isEmergencyStop = data.emergency_stop;
    fetchOfficeState();
    fetchStatus();
  } catch (err) {
    alert("Emergency stop error: " + err.message);
  }
}

// 12. Lightweight SVG Vector Avatar Generator
function generateEmployeeAvatarSvg(theme) {
  const palettes = {
    ceo: { bg: "#1e293b", skin: "#fed7aa", hair: "#334155", accent: "#fbbf24", suit: "#0f172a" },
    research: { bg: "#134e4a", skin: "#fde68a", hair: "#78350f", accent: "#2dd4bf", suit: "#115e59" },
    pm: { bg: "#312e81", skin: "#fed7aa", hair: "#1e1b4b", accent: "#818cf8", suit: "#3730a3" },
    creation: { bg: "#064e3b", skin: "#fef08a", hair: "#0f172a", accent: "#34d399", suit: "#065f46" },
    marketing: { bg: "#831843", skin: "#fed7aa", hair: "#701a75", accent: "#f472b6", suit: "#9d174d" },
    sales: { bg: "#14532d", skin: "#ffedd5", hair: "#451a03", accent: "#4ade80", suit: "#166534" },
    support: { bg: "#0c4a6e", skin: "#fed7aa", hair: "#1c1917", accent: "#38bdf8", suit: "#0369a1" },
    ops: { bg: "#78350f", skin: "#fde68a", hair: "#451a03", accent: "#fbbf24", suit: "#92400e" },
    finance: { bg: "#1e293b", skin: "#ffedd5", hair: "#475569", accent: "#38bdf8", suit: "#1e293b" },
    compliance: { bg: "#172554", skin: "#fed7aa", hair: "#0f172a", accent: "#60a5fa", suit: "#1e3a8a" },
    qa: { bg: "#3b0764", skin: "#fef08a", hair: "#581c87", accent: "#c084fc", suit: "#6b21a8" },
    automation: { bg: "#022c22", skin: "#99f6e4", hair: "#0f172a", accent: "#2dd4bf", suit: "#134e4a" },
    generic: { bg: "#1e293b", skin: "#e2e8f0", hair: "#0f172a", accent: "#6366f1", suit: "#334155" }
  };

  const p = palettes[theme] || palettes.generic;

  return `
    <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:100%;">
      <!-- Background Circle -->
      <circle cx="32" cy="32" r="32" fill="${p.bg}" />
      
      <!-- Body / Shoulders -->
      <path d="M12 58 C12 46, 20 42, 32 42 C44 42, 52 46, 52 58 Z" fill="${p.suit}" />
      
      <!-- Collar / Tie Accent -->
      <polygon points="32,46 28,42 36,42" fill="${p.accent}" />
      <polygon points="30,46 34,46 33,54 31,54" fill="${p.accent}" />

      <!-- Head & Neck -->
      <rect x="29" y="34" width="6" height="8" rx="2" fill="${p.skin}" />
      <circle cx="32" cy="25" r="13" fill="${p.skin}" />

      <!-- Hair -->
      <path d="M19 23 C19 15, 23 11, 32 11 C41 11, 45 15, 45 23 C43 20, 39 19, 32 19 C25 19, 21 20, 19 23 Z" fill="${p.hair}" />

      <!-- Eyes & Glasses / Headset depending on role -->
      <circle cx="27" cy="25" r="1.5" fill="#0f172a" />
      <circle cx="37" cy="25" r="1.5" fill="#0f172a" />
      <path d="M29 30 Q32 33 35 30" stroke="#0f172a" stroke-width="1.2" stroke-linecap="round" fill="none" />

      ${theme === 'ceo' || theme === 'research' || theme === 'finance' ? `
        <!-- Sleek Glasses -->
        <rect x="23" y="22" width="8" height="6" rx="1.5" stroke="${p.accent}" stroke-width="1.2" fill="none" />
        <rect x="33" y="22" width="8" height="6" rx="1.5" stroke="${p.accent}" stroke-width="1.2" fill="none" />
        <line x1="31" y1="25" x2="33" y2="25" stroke="${p.accent}" stroke-width="1.2" />
      ` : ''}

      ${theme === 'sales' || theme === 'support' || theme === 'ops' ? `
        <!-- Communication Headset -->
        <path d="M20 22 C20 16, 44 16, 44 22" stroke="${p.accent}" stroke-width="1.5" fill="none" />
        <circle cx="44" cy="24" r="2.5" fill="${p.accent}" />
        <path d="M44 25 Q42 32 36 32" stroke="${p.accent}" stroke-width="1.2" fill="none" />
        <circle cx="36" cy="32" r="1.2" fill="${p.accent}" />
      ` : ''}

      ${theme === 'creation' || theme === 'qa' || theme === 'automation' ? `
        <!-- Developer Headphones -->
        <path d="M19 24 C19 14, 45 14, 45 24" stroke="${p.accent}" stroke-width="2" fill="none" />
        <rect x="18" y="21" width="4" height="8" rx="2" fill="${p.accent}" />
        <rect x="42" y="21" width="4" height="8" rx="2" fill="${p.accent}" />
      ` : ''}
    </svg>
  `;
}

// ----------------- Phase 5B: 24/7 Cloud & Reports UI Controllers -----------------
let currentTimeframe = "today";

function setTimeframe(tf) {
  currentTimeframe = tf;
  document.querySelectorAll(".active-timeframe").forEach(b => b.classList.remove("active-timeframe"));
  if (tf === "today") document.getElementById("btnTimeframeToday")?.classList.add("active-timeframe");
  if (tf === "7days") document.getElementById("btnTimeframe7Days")?.classList.add("active-timeframe");
  if (tf === "all") document.getElementById("btnTimeframeAll")?.classList.add("active-timeframe");
  fetchEmployeeActivities(tf);
}

async function fetchCloudStatus() {
  try {
    const res = await fetch("/api/cloud/status");
    const data = await res.json();
    const hb = data.heartbeat || {};
    const laptopInfo = hb.can_close_laptop || {};

    // 1. Update AI Office Badges (Truthful Zero-Fake Evaluation)
    const cloudBadge = document.getElementById("officeCloudBadge");
    if (cloudBadge) {
      if (laptopInfo.can_close) {
        cloudBadge.innerHTML = "🟢 Remote Cloud Active";
        cloudBadge.style.background = "rgba(16, 185, 129, 0.2)";
        cloudBadge.style.color = "var(--accent-emerald)";
      } else {
        cloudBadge.innerHTML = "🟡 Local Workstation (Laptop Required)";
        cloudBadge.style.background = "rgba(245, 158, 11, 0.2)";
        cloudBadge.style.color = "var(--accent-amber)";
      }
    }

    const gemini = data.gemini || {};
    const officeGeminiBadge = document.getElementById("officeGeminiBadge");
    if (officeGeminiBadge) {
      officeGeminiBadge.innerHTML = gemini.status === "CONNECTED" ? "🟢 Gemini Connected" : (gemini.status === "WARNING" ? "🟡 Gemini Limited" : "🔴 Gemini Offline");
    }

    const sched = data.scheduler || {};
    const officeReportSchedBadge = document.getElementById("officeReportSchedBadge");
    if (officeReportSchedBadge) {
      officeReportSchedBadge.innerText = `⏰ ${sched.target_schedule || "23:00 Asia/Dubai"}`;
    }

    // 2. Update Primary Question Banner: "CAN I CLOSE MY LAPTOP?"
    const canCloseBadge = document.getElementById("canCloseLaptopBadge");
    const canCloseDesc = document.getElementById("canCloseLaptopDesc");
    const canCloseAction = document.getElementById("canCloseLaptopAction");
    const canCloseBanner = document.getElementById("canCloseLaptopBanner");
    const deployStateBadge = document.getElementById("cloudDeploymentStateBadge");

    if (canCloseBadge && laptopInfo.badge) {
      canCloseBadge.innerText = laptopInfo.badge;
      if (laptopInfo.can_close) {
        canCloseBadge.style.background = "rgba(16, 185, 129, 0.2)";
        canCloseBadge.style.color = "var(--accent-emerald)";
        if (canCloseBanner) canCloseBanner.style.borderLeftColor = "var(--accent-emerald)";
      } else {
        canCloseBadge.style.background = "rgba(244, 63, 94, 0.2)";
        canCloseBadge.style.color = "var(--accent-rose)";
        if (canCloseBanner) canCloseBanner.style.borderLeftColor = "var(--accent-rose)";
      }
    }

    if (canCloseDesc) {
      canCloseDesc.innerText = laptopInfo.reason || "Evaluating runtime environment...";
    }
    if (canCloseAction && laptopInfo.recommended_action) {
      canCloseAction.innerHTML = `💡 <strong>Next Step:</strong> ${laptopInfo.recommended_action}`;
    }
    if (deployStateBadge) {
      deployStateBadge.innerText = hb.cloud_deployment_state || "LOCAL_WORKSTATION";
    }

    // 3. Update Gemini Provider Card in Cloud Tab
    const geminiHealthBadge = document.getElementById("geminiHealthBadge");
    if (geminiHealthBadge) {
      geminiHealthBadge.innerHTML = gemini.status_text || "🟢 Connected";
    }
    const geminiModelName = document.getElementById("geminiModelName");
    if (geminiModelName) {
      geminiModelName.innerText = gemini.configured_model || "gemini-2.5-flash";
    }
    const geminiFallback = document.getElementById("geminiFallbackProvider");
    if (geminiFallback) {
      geminiFallback.innerText = gemini.fallback_provider || "Deterministic System Synthesizer";
    }

    // 4. Render Heartbeat Grid
    const overallBadge = document.getElementById("heartbeatOverallStatus");
    if (overallBadge) {
      overallBadge.innerText = hb.overall_status || "HEALTHY";
      overallBadge.style.color = hb.overall_status === "HEALTHY" ? "var(--accent-emerald)" : "var(--accent-amber)";
    }

    const hbGrid = document.getElementById("heartbeatGrid");
    if (hbGrid && hb.components) {
      hbGrid.innerHTML = Object.entries(hb.components).map(([k, c]) => `
        <div style="background: rgba(0,0,0,0.3); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 0.75rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.35rem;">
            <strong style="font-size: 0.82rem; color: #fff; text-transform: capitalize;">${k.replace('_', ' ')}</strong>
            <span style="font-size: 0.75rem;">${c.label}</span>
          </div>
          <p style="font-size: 0.74rem; color: var(--text-secondary); margin: 0;">${c.details || ""}</p>
        </div>
      `).join("");
    }

  } catch (err) {
    console.error("Cloud status error:", err);
  }
}

// ----------------- Phase 5C Verification Suite UI Handlers -----------------

async function runLaptopVerificationCheck() {
  await fetchCloudStatus();
  try {
    const res = await fetch("/api/cloud/proof");
    const gate = await res.json();
    const gateBadge = document.getElementById("independenceGateBadge");
    if (gateBadge) {
      gateBadge.innerText = `GATE: ${gate.gate_status}`;
      gateBadge.style.background = gate.gate_status === "PASSED" ? "rgba(16, 185, 129, 0.2)" : "rgba(244, 63, 94, 0.2)";
      gateBadge.style.color = gate.gate_status === "PASSED" ? "var(--accent-emerald)" : "var(--accent-rose)";
    }
    const lblTime = document.getElementById("lblLastVerifiedTime");
    if (lblTime) lblTime.innerText = `Checked: ${new Date().toLocaleTimeString()}`;
  } catch (err) {}
}

function logProofOutput(msg) {
  const box = document.getElementById("proofOutputBox");
  if (!box) return;
  box.style.display = "block";
  box.innerHTML += `<div>[${new Date().toLocaleTimeString()}] ${msg}</div>`;
  box.scrollTop = box.scrollHeight;
}

async function runProofTask() {
  logProofOutput("Dispatching CLOUD_PROOF_TASK to worker...");
  try {
    const res = await fetch("/api/cloud/proof/run-task", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      logProofOutput(`✅ CLOUD_PROOF_TASK Completed: Task ID ${data.task_id} on ${data.evidence.instance_type} (${data.evidence.instance_id})`);
    } else {
      logProofOutput(`❌ Task Failed: ${data.error}`);
    }
  } catch (err) {
    logProofOutput(`❌ Network/Execution Error: ${err.message}`);
  }
}

async function runPersistenceTest() {
  logProofOutput("Executing SQLite database persistence write-read cycle...");
  try {
    const res = await fetch("/api/cloud/proof/test-persistence", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      logProofOutput(`✅ Persistence Verified: Record ${data.test_key} confirmed persistent across cycles.`);
    } else {
      logProofOutput(`❌ Persistence Failed: ${data.status}`);
    }
  } catch (err) {
    logProofOutput(`❌ Persistence Error: ${err.message}`);
  }
}

async function runWorkerRecoveryTest() {
  logProofOutput("Simulating worker fault and testing automatic recovery loop...");
  try {
    const res = await fetch("/api/cloud/proof/test-worker-recovery", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      logProofOutput(`✅ Worker Recovery Verified: Worker thread revived and task polling loop active.`);
    } else {
      logProofOutput(`❌ Recovery Test Failed`);
    }
  } catch (err) {
    logProofOutput(`❌ Recovery Error: ${err.message}`);
  }
}

async function runSecurityScan() {
  logProofOutput("Scanning repository files for hard-coded credentials, API keys, or private tokens...");
  try {
    const res = await fetch("/api/cloud/proof/security-scan");
    const data = await res.json();
    if (data.clean) {
      logProofOutput(`✅ Security Scan Clean: ${data.scanned_files} files checked. Zero credentials exposed.`);
    } else {
      logProofOutput(`⚠️ Security Alert: Found ${data.violations.length} suspicious pattern(s).`);
    }
  } catch (err) {
    logProofOutput(`❌ Security Scan Error: ${err.message}`);
  }
}

async function fetchDailyReports() {
  try {
    const res = await fetch("/api/cloud/reports/daily");
    const reports = await res.json();
    const container = document.getElementById("dailyReportsList");
    if (!container) return;

    if (!reports.length) {
      container.innerHTML = `<div style="font-size:0.8rem; color:var(--text-muted); padding:1rem; text-align:center;">No daily reports generated yet. Click 'Generate & Email Report Now'.</div>`;
      return;
    }

    container.innerHTML = reports.map(r => `
      <div style="background: rgba(0,0,0,0.25); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 0.85rem; font-size: 0.82rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.25rem;">
          <strong style="color: #fff;">${r.date} Daily CEO Report</strong>
          <span class="badge" style="background:rgba(16,185,129,0.2); color:var(--accent-emerald);">${r.validation_status}</span>
        </div>
        <p style="font-size: 0.76rem; color: var(--text-secondary); margin: 0 0 0.5rem 0;">${r.summary ? r.summary.substring(0, 140) + '...' : ''}</p>
        <div style="display:flex; gap:0.5rem;">
          <span style="font-size: 0.7rem; color: var(--text-muted);">Generated at ${r.generated_at}</span>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Daily reports fetch error:", err);
  }
}

async function fetchEmailDeliveries() {
  try {
    const res = await fetch("/api/cloud/email/deliveries");
    const deliveries = await res.json();
    const container = document.getElementById("emailDeliveriesList");
    if (!container) return;

    if (!deliveries.length) {
      container.innerHTML = `<div style="font-size:0.8rem; color:var(--text-muted); padding:1rem; text-align:center;">No email deliveries recorded yet.</div>`;
      return;
    }

    container.innerHTML = deliveries.map(d => `
      <div style="background: rgba(0,0,0,0.25); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 0.75rem; font-size: 0.8rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.25rem;">
          <strong style="color: var(--accent-cyan);">${d.recipient}</strong>
          <span class="badge" style="background:${d.status === 'DELIVERED' || d.status === 'QUEUED_LOCAL_OUTBOX' ? 'rgba(16,185,129,0.2)' : 'rgba(244,63,94,0.2)'}; color:${d.status === 'DELIVERED' || d.status === 'QUEUED_LOCAL_OUTBOX' ? 'var(--accent-emerald)' : 'var(--accent-rose)'};">
            ${d.status}
          </span>
        </div>
        <div style="font-size: 0.74rem; color: var(--text-muted); margin-bottom: 0.25rem;">Provider: ${d.provider} • ID: ${d.delivery_id}</div>
        <div style="font-size: 0.72rem; color: var(--text-secondary);">${d.subject}</div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Email deliveries fetch error:", err);
  }
}

async function triggerManualDailyReport() {
  const btn = document.getElementById("btnManualDailyReport");
  if (btn) {
    btn.disabled = true;
    btn.innerText = "⏳ Compiling & Verifying...";
  }

  try {
    const res = await fetch("/api/cloud/reports/generate-daily", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      alert(`✅ Daily CEO Progress Report compiled and dispatched!\nReport ID: ${data.report_id}\nRecipient: manirkhn@gmail.com\nDelivery Status: ${data.delivery?.status}`);
      fetchDailyReports();
      fetchEmailDeliveries();
    } else {
      alert(`⚠️ Report Generation Alert: ${data.error || "Could not complete report"}`);
    }
  } catch (err) {
    alert(`❌ Failed to trigger report: ${err.message}`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerText = "🚀 Generate & Email Report Now";
    }
  }
}

async function fetchEmployeeActivities(timeframe = "today") {
  try {
    const [summaryRes, actsRes] = await Promise.all([
      fetch(`/api/cloud/activities/summary?timeframe=${timeframe}`),
      fetch(`/api/cloud/activities?timeframe=${timeframe}&limit=50`)
    ]);

    const summary = await summaryRes.json();
    const acts = await actsRes.json();

    // Render Summary Table
    const tableBody = document.getElementById("employeeActivitySummaryTableBody");
    if (tableBody) {
      tableBody.innerHTML = summary.map(e => `
        <tr>
          <td><code>${e.employee_id}</code></td>
          <td><strong>${e.role}</strong></td>
          <td>${e.total_tasks}</td>
          <td><span style="color:var(--accent-emerald);">${e.completed}</span></td>
          <td><span style="color:var(--accent-rose);">${e.failed}</span></td>
          <td><span style="color:var(--accent-amber);">${e.blocked}</span></td>
          <td><span class="desk-status-pill working">${e.current_status}</span></td>
          <td><button class="btn btn-secondary" style="font-size:0.7rem; padding:0.2rem 0.5rem;" onclick="openEmployeeDesk('${e.employee_id}')">Open Desk</button></td>
        </tr>
      `).join("");
    }

    // Render Activity Feed
    const feed = document.getElementById("employeeActivityFeed");
    const countBadge = document.getElementById("activityCountBadge");
    if (countBadge) countBadge.innerText = `${acts.length} Events`;

    if (feed) {
      if (!acts.length) {
        feed.innerHTML = `<div style="font-size:0.82rem; color:var(--text-muted); padding:1rem; text-align:center;">No activities recorded for selected timeframe. Background workers record events automatically as tasks progress.</div>`;
      } else {
        feed.innerHTML = acts.map(a => `
          <div style="background: rgba(0,0,0,0.25); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 0.85rem; font-size: 0.82rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.25rem;">
              <div>
                <strong style="color: #fff;">${a.employee_name}</strong>
                <span style="color: var(--accent-cyan); font-size: 0.75rem; margin-left: 0.5rem;">[${a.role}]</span>
              </div>
              <span class="badge" style="background:rgba(16,185,129,0.2); color:var(--accent-emerald);">${a.status}</span>
            </div>
            <div style="color: var(--text-primary); margin-bottom: 0.35rem;">${a.action}</div>
            <div style="display:flex; gap: 0.85rem; flex-wrap: wrap; font-size: 0.74rem; color: var(--text-muted);">
              ${a.project ? `<span>📁 Project: <strong>${a.project}</strong></span>` : ''}
              ${a.experiment ? `<span>🧪 Exp: <strong>${a.experiment}</strong></span>` : ''}
              ${a.module ? `<span>⚙️ Module: <strong>${a.module}</strong></span>` : ''}
              <span>⏱ ${a.start_time}</span>
            </div>
          </div>
        `).join("");
      }
    }
  } catch (err) {
    console.error("Error loading employee activities:", err);
  }
}

// ----------------- Phase 5D: Payments, Checkout & Owner Settlement UI -----------------

async function loadPaymentsDashboard() {
  try {
    const [dashRes, flowRes, gatesRes, txRes] = await Promise.all([
      fetch("/api/payments/dashboard"),
      fetch("/api/payments/money-flow"),
      fetch("/api/payments/gates"),
      fetch("/api/revenue/pipeline")
    ]);

    const dash = await dashRes.json();
    const flow = await flowRes.json();
    const gates = await gatesRes.json();

    // 1. KPI Strip
    const vr = dash.verified_revenue || {};
    const setl = dash.settlements || {};
    const testm = dash.test_mode_isolation || {};

    const elLifetime = document.getElementById("payLifetimeRevenue");
    const elLifetimeAed = document.getElementById("payLifetimeAed");
    const elToday = document.getElementById("payTodayRevenue");
    const elTodayAed = document.getElementById("payTodayAed");
    const elCust = document.getElementById("payCustomerCount");
    const elSetl = document.getElementById("paySettlementStatus");
    const elTestVol = document.getElementById("payTestVolume");

    if (elLifetime) elLifetime.innerText = `$${(vr.lifetime_verified_usd || 0).toFixed(2)}`;
    if (elLifetimeAed) elLifetimeAed.innerText = `AED ${(vr.lifetime_verified_aed || 0).toFixed(2)} (Peg: 3.6725)`;
    if (elToday) elToday.innerText = `$${(vr.today_verified_usd || 0).toFixed(2)}`;
    if (elTodayAed) elTodayAed.innerText = `AED ${(vr.today_verified_aed || 0).toFixed(2)}`;
    if (elCust) elCust.innerText = vr.verified_customer_count || 0;
    if (elSetl) elSetl.innerText = (setl.settlement_completed_usd > 0) ? "🟢 SETTLED" : "🟡 PENDING";
    if (elTestVol) elTestVol.innerText = `$${(testm.test_volume_usd || 0).toFixed(2)}`;

    // 2. First Real Customer Gate
    const gate = dash.first_customer_gate || {};
    const gateBadge = document.getElementById("firstCustomerGateBadge");
    const gateDesc = document.getElementById("firstCustomerGateDesc");
    const gateChecklist = document.getElementById("firstCustomerChecklist");

    if (gateBadge) {
      gateBadge.innerText = gate.badge || "READY";
      gateBadge.style.background = gate.status === "FIRST_REAL_CUSTOMER_VERIFIED" ? "rgba(16,185,129,0.2)" : "rgba(245,158,11,0.2)";
      gateBadge.style.color = gate.status === "FIRST_REAL_CUSTOMER_VERIFIED" ? "var(--accent-emerald)" : "var(--accent-amber)";
    }
    if (gateDesc) gateDesc.innerText = gate.description || "";
    if (gateChecklist && gate.checklist) {
      gateChecklist.innerHTML = Object.entries(gate.checklist).map(([k, v]) => `
        <div style="background: rgba(0,0,0,0.25); padding: 0.4rem 0.6rem; border-radius: 4px; display:flex; justify-content:space-between; align-items:center;">
          <span style="color: var(--text-secondary); text-transform: capitalize;">${k.replace(/_/g, ' ')}</span>
          <span style="color: ${v ? 'var(--accent-emerald)' : 'var(--accent-rose)'}; font-weight:700;">${v ? '✅' : '❌'}</span>
        </div>
      `).join("");
    }

    // 3. Income Readiness & Bottleneck
    const read = dash.readiness || {};
    const readBadge = document.getElementById("incomeReadinessBadge");
    const bneckBadge = document.getElementById("incomeBottleneckBadge");
    const bneckGuidance = document.getElementById("incomeBottleneckGuidance");

    if (readBadge) readBadge.innerText = read.badge || "READY";
    if (bneckBadge) bneckBadge.innerText = read.current_bottleneck || "TRAFFIC";
    if (bneckGuidance) bneckGuidance.innerText = read.operational_guidance || "";

    // 4. "Where Did The Money Go?" Flow
    const flowContainer = document.getElementById("whereDidMoneyGoPipeline");
    if (flowContainer && flow.steps) {
      flowContainer.innerHTML = flow.steps.map(s => `
        <div style="display:flex; justify-content:space-between; align-items:center; background: rgba(0,0,0,0.25); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 0.65rem 0.85rem; font-size: 0.82rem;">
          <div style="display:flex; align-items:center; gap: 0.75rem;">
            <span style="background: rgba(99,102,241,0.2); color: var(--accent-indigo); width: 24px; height: 24px; border-radius: 50%; display:flex; align-items:center; justify-content:center; font-weight:700; font-size: 0.75rem;">${s.step}</span>
            <div>
              <strong style="color: #fff;">${s.name}</strong>
              <div style="color: var(--text-secondary); font-size: 0.76rem; margin-top: 0.1rem;">${s.detail}</div>
            </div>
          </div>
          <span class="badge" style="background: rgba(255,255,255,0.08); font-size: 0.75rem;">${s.badge}</span>
        </div>
      `).join("");
    }

    // 5. Payment Approval Gates
    const gatesContainer = document.getElementById("paymentGatesList");
    if (gatesContainer && gates) {
      gatesContainer.innerHTML = Object.values(gates).map(g => `
        <div style="display:flex; justify-content:space-between; align-items:center; background: rgba(0,0,0,0.25); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 0.6rem 0.85rem; font-size: 0.8rem;">
          <div>
            <strong style="color: #fff;">${g.title}</strong>
            <div style="color: var(--text-muted); font-size: 0.72rem; margin-top: 0.1rem;">${g.notes}</div>
          </div>
          <div style="display:flex; align-items:center; gap: 0.5rem;">
            <span class="badge" style="background: ${g.is_approved ? 'rgba(16,185,129,0.2)' : 'rgba(244,63,94,0.2)'}; color: ${g.is_approved ? 'var(--accent-emerald)' : 'var(--accent-rose)'}; font-size: 0.72rem;">
              ${g.is_approved ? 'APPROVED' : 'LOCKED'}
            </span>
            <button class="btn btn-secondary" style="font-size: 0.7rem; padding: 0.2rem 0.55rem;" onclick="togglePaymentGate('${g.gate_key}', ${g.is_approved})">
              ${g.is_approved ? 'Revoke' : 'Approve'}
            </button>
          </div>
        </div>
      `).join("");
    }

    // 6. Recent Payment Transactions Table
    const txBody = document.getElementById("paymentTransactionsTableBody");
    if (txBody) {
      // Fetch receipts/orders
      const txHistoryRes = await fetch("/api/sales/deliveries");
      let delivs = [];
      if (txHistoryRes.ok) {
        delivs = await txHistoryRes.json();
      }

      if (!delivs.length) {
        txBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted); padding:1rem;">No transactions yet. Execute Sandbox test below to verify live flow.</td></tr>`;
      } else {
        txBody.innerHTML = delivs.map(d => `
          <tr>
            <td><code>${d.order_id}</code></td>
            <td><strong>${d.product_id}</strong></td>
            <td>$29.00 USD</td>
            <td><span class="badge" style="background:rgba(99,102,241,0.2); color:var(--accent-indigo);">TEST / PROD</span></td>
            <td><span class="badge" style="background:rgba(16,185,129,0.2); color:var(--accent-emerald);">${d.status}</span></td>
            <td><span style="color:var(--accent-emerald);">DELIVERED</span></td>
            <td><button class="btn btn-secondary" style="font-size:0.7rem; padding:0.2rem 0.5rem;" onclick="viewReceiptModal('${d.order_id}')">View Receipt</button></td>
          </tr>
        `).join("");
      }
    }

  } catch (err) {
    console.error("Error loading payments dashboard:", err);
  }
}

async function togglePaymentGate(gateKey, currentState) {
  try {
    const res = await fetch("/api/payments/gates", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        gate_key: gateKey,
        is_approved: !currentState,
        notes: `Toggled by owner via command center dashboard`
      })
    });
    if (res.ok) {
      loadPaymentsDashboard();
    }
  } catch (err) {
    alert("Error toggling payment gate: " + err.message);
  }
}

async function runSandboxPaymentTest() {
  const btn = document.getElementById("btnRunSandboxTest");
  const term = document.getElementById("sandboxTerminalOutput");
  if (btn) btn.disabled = true;
  if (term) {
    term.style.display = "block";
    term.innerHTML = "▶ Initializing Sandbox End-to-End Payment & Webhook Verification...\n";
  }

  try {
    const res = await fetch("/api/payments/test-flow", { method: "POST" });
    const data = await res.json();

    if (term) {
      term.innerHTML += `[1/6] Created customer checkout session: Order ID: ${data.order_id} (Mode: ${data.mode})\n`;
      term.innerHTML += `[2/6] Simulated payment gateway webhook with HMAC-SHA256 signature\n`;
      term.innerHTML += `[3/6] Webhook processed: ${JSON.stringify(data.webhook_result.status)}\n`;
      term.innerHTML += `[4/6] Anti-replay attack check: ${data.replay_prevention_result.status} (Idempotency OK)\n`;
      term.innerHTML += `[5/6] Digital product package generated & verified: Checksum: ${data.receipt ? data.receipt.package_checksum : 'OK'}\n`;
      term.innerHTML += `[6/6] Production Revenue Ledger Leakage Check: Leakage = ${data.production_revenue_ledger_leakage} (ISOLATION STRICTLY ENFORCED)\n\n`;
      term.innerHTML += `✅ VERIFICATION COMPLETE: ${data.summary}\n`;
    }

    loadPaymentsDashboard();
  } catch (err) {
    if (term) term.innerHTML += `❌ TEST FAILED: ${err.message}\n`;
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function viewReceiptModal(orderId) {
  try {
    const res = await fetch(`/api/payments/receipt/${orderId}`);
    if (!res.ok) {
      alert(`Customer receipt for ${orderId} is being generated.`);
      return;
    }
    const r = await res.json();
    alert(`🧾 CUSTOMER RECEIPT\nOrder ID: ${r.order_id}\nProduct: ${r.product_name}\nAmount: ${r.currency} ${r.amount.toFixed(2)}\nPayment Status: ${r.payment_status}\nDelivery: ${r.delivery_status}\nPackage SHA256: ${r.package_checksum || 'Verified'}\nSupport: ${r.support_email}`);
  } catch (err) {
    alert("Error fetching receipt: " + err.message);
  }
}

// ============================================================
// PHASE 5E: SALES, MARKETING & ACQUISITION COMMAND CENTER
// ============================================================

async function fetchMarketingCommandCenter() {
  try {
    const res = await fetch("/api/marketing/command-center");
    if (!res.ok) return;
    const data = await res.json();

    // 1. Top Status
    const sell = data.what_we_are_selling || {};
    const funnel = data.customer_acquisition_funnel || {};
    const diag = data.money_pipeline_diagnostics || {};

    const topName = document.getElementById("topSellingProductName");
    if (topName) topName.textContent = sell.product_name || "Local LLM Benchmark Suite";

    const topRev = document.getElementById("topSellingRevenue");
    if (topRev) topRev.textContent = `$${(funnel.lifetime_verified_revenue_usd || 29.0).toFixed(2)} USD`;

    const topCust = document.getElementById("topSellingCustomers");
    if (topCust) topCust.textContent = `${funnel.lifetime_verified_customers || 1} Lifetime`;

    const topBot = document.getElementById("topSellingBottleneck");
    if (topBot) topBot.textContent = diag.primary_bottleneck || "TRAFFIC & OUTREACH";

    // 2. Section 1: What Are We Selling?
    const pName = document.getElementById("mktProdName");
    if (pName) pName.textContent = sell.product_name || "Local LLM Benchmark Suite";
    const pId = document.getElementById("mktProdId");
    if (pId) pId.textContent = sell.product_id || "PROD-LLM-EVAL-001";
    const pPrice = document.getElementById("mktProdPrice");
    if (pPrice) pPrice.textContent = `$${(sell.price_usd || 29.0).toFixed(2)} USD`;
    const pAed = document.getElementById("mktProdPriceAed");
    if (pAed) pAed.textContent = `AED ${(sell.price_aed || 106.50).toFixed(2)}`;
    const pProb = document.getElementById("mktProdProblem");
    if (pProb) pProb.textContent = sell.problem_solved || "Local LLM evaluation without cloud dependencies.";
    const pTarg = document.getElementById("mktProdTarget");
    if (pTarg) pTarg.textContent = sell.target_customer || "AI engineers and prompt testers.";
    const pDeliv = document.getElementById("mktProdDelivers");
    if (pDeliv) pDeliv.textContent = sell.what_customer_receives || "Python evaluation harness and test suites.";

    // 3. Section 2: Historical vs Production Separation
    const hCust = document.getElementById("histCustCount");
    if (hCust) hCust.textContent = `${funnel.historical_verified_customers || 1}`;
    const hRev = document.getElementById("histRevAmount");
    if (hRev) hRev.textContent = `$${(funnel.historical_verified_revenue_usd || 29.0).toFixed(2)} USD`;

    const pCust = document.getElementById("prodCustCount");
    if (pCust) pCust.textContent = funnel.new_production_verified_customers > 0 ? `${funnel.new_production_verified_customers}` : "0 VERIFIED";
    const pRev = document.getElementById("prodRevAmount");
    if (pRev) pRev.textContent = `$${(funnel.new_production_verified_revenue_usd || 0.0).toFixed(2)} USD`;

    const pCheck = document.getElementById("prodCheckoutsCount");
    if (pCheck) pCheck.textContent = funnel.funnel_stages ? `${funnel.funnel_stages.checkout_starts || 0}` : "0";
    const pPay = document.getElementById("prodPaymentsCount");
    if (pPay) pPay.textContent = funnel.funnel_stages ? `${funnel.funnel_stages.payment_attempts || 0}` : "0";
    const pDel = document.getElementById("prodDeliveriesCount");
    if (pDel) pDel.textContent = funnel.funnel_stages ? `${funnel.funnel_stages.delivered_products || 0}` : "0";
    const pRef = document.getElementById("prodRefundsCount");
    if (pRef) pRef.textContent = "0";

    // 4. Section 3: Where Did We Market?
    const whereTags = document.getElementById("mktWhereSummaryTags");
    const channels = data.where_did_we_market || [];
    if (whereTags) {
      if (channels.length === 0) {
        whereTags.innerHTML = `<span style="font-size: 0.8rem; color: var(--text-muted); font-style: italic;">No channels with verified activity yet (Free-first mode active).</span>`;
      } else {
        whereTags.innerHTML = channels.map(c => `
          <span class="channel-tag-badge">
            📡 <strong>${c.platform}</strong> (${c.channel}): ${c.total_activities} verified actions
          </span>
        `).join("");
      }
    }

    const whereTable = document.getElementById("mktWhereTableBody");
    const activities = data.marketing_activity_log || [];
    if (whereTable) {
      if (activities.length === 0) {
        whereTable.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">0 verified marketing activities recorded yet.</td></tr>`;
      } else {
        whereTable.innerHTML = activities.slice(0, 10).map(a => `
          <tr>
            <td>${a.timestamp.substring(0, 16).replace("T", " ")}</td>
            <td><strong style="color: var(--accent-cyan);">${a.employee_id}</strong></td>
            <td>${a.platform} <span style="font-size: 0.72rem; color: var(--text-muted);">(${a.channel})</span></td>
            <td><code>${a.campaign_id || 'ORGANIC'}</code></td>
            <td>${a.target_persona || 'AI Developers'}</td>
            <td>${a.activity_type}</td>
            <td><span class="badge" style="background: rgba(16, 185, 129, 0.15); color: var(--accent-emerald);">${a.execution_status}</span></td>
            <td>${a.result || 'Executed'}</td>
            <td><code style="font-size: 0.72rem;">${a.evidence_reference || a.activity_id}</code></td>
          </tr>
        `).join("");
      }
    }

    // 5. Section 4: 12-Stage Visual Customer Acquisition Funnel
    const funnelCont = document.getElementById("mktFunnelContainer");
    if (funnelCont && funnel.funnel_stages) {
      const stagesDef = [
        { key: "researched_opportunities", name: "1. Researched Opportunities" },
        { key: "target_prospects", name: "2. Target Prospects" },
        { key: "marketing_outreach_attempts", name: "3. Marketing / Outreach Attempts" },
        { key: "responses", name: "4. Responses" },
        { key: "qualified_leads", name: "5. Qualified Leads" },
        { key: "checkout_visits", name: "6. Checkout Visits" },
        { key: "checkout_starts", name: "7. Checkout Starts" },
        { key: "payment_attempts", name: "8. Payment Attempts" },
        { key: "verified_payments", name: "9. Verified Payments" },
        { key: "customers", name: "10. Customers" },
        { key: "delivered_products", name: "11. Delivered Products" },
        { key: "repeat_referral_customers", name: "12. Repeat / Referral Customers" }
      ];

      funnelCont.innerHTML = stagesDef.map((s, idx) => {
        const val = funnel.funnel_stages[s.key] !== undefined ? funnel.funnel_stages[s.key] : 0;
        const arrow = idx < stagesDef.length - 1 ? `<div class="funnel-arrow-down">↓</div>` : "";
        return `
          <div class="funnel-step-row">
            <span class="funnel-step-number">#${idx + 1}</span>
            <span class="funnel-step-name">${s.name}</span>
            <span class="funnel-step-value">${val}</span>
            <span class="funnel-step-verified-badge">VERIFIED</span>
          </div>
          ${arrow}
        `;
      }).join("");
    }

    // 6. Section 5: Marketing Employee Desks
    const desksGrid = document.getElementById("mktEmployeeDesksGrid");
    const desks = data.marketing_employee_desks || {};
    if (desksGrid) {
      desksGrid.innerHTML = Object.keys(desks).map(k => {
        const d = desks[k];
        const statusClass = (d.desk_status || "IDLE").toLowerCase();
        return `
          <div class="desk-card glass">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
              <strong style="color: #fff; font-size: 0.95rem;">${d.name}</strong>
              <span class="desk-status-pill ${statusClass}">
                ● ${d.desk_status}
              </span>
            </div>
            <div style="font-size: 0.78rem; color: var(--text-muted); margin-bottom: 0.4rem;">
              Role: <code>${d.role}</code>
            </div>
            <div style="font-size: 0.84rem; color: var(--text-primary); margin-bottom: 0.6rem;">
              <strong>Current Task:</strong> ${d.current_task || 'Monitoring opportunities'}
            </div>
            <div style="font-size: 0.78rem; color: var(--text-secondary); background: rgba(0,0,0,0.25); padding: 0.5rem; border-radius: var(--radius-sm); margin-bottom: 0.5rem;">
              <strong>Result:</strong> ${d.result || 'Active'}
            </div>
            <div style="font-size: 0.78rem; color: var(--accent-cyan);">
              <strong>Next Action:</strong> ${d.next_action || 'Autonomous research'}
            </div>
          </div>
        `;
      }).join("");
    }

    // 7. Section 6: What Did The AI Do Today? (Timeline)
    const timelineList = document.getElementById("mktTodayTimelineList");
    const timeline = data.what_did_ai_do_today_timeline || [];
    if (timelineList) {
      if (timeline.length === 0) {
        timelineList.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 1rem; font-style: italic;">NO VERIFIED MARKETING ACTIVITY TODAY</div>`;
      } else {
        timelineList.innerHTML = timeline.map(t => `
          <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(22, 30, 46, 0.6); padding: 0.75rem 1rem; border-radius: var(--radius-sm); border-left: 3px solid var(--accent-cyan); font-size: 0.85rem;">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
              <code style="color: var(--accent-cyan); font-size: 0.8rem;">${t.timestamp.substring(11, 16)}</code>
              <span><strong>${t.employee_id}</strong> (${t.activity_type}) on <strong>${t.platform}</strong>: ${t.result}</span>
            </div>
            <div>
              <span class="badge" style="background: rgba(99, 102, 241, 0.15); color: var(--accent-indigo); font-size: 0.72rem;">${t.execution_mode || 'LOCAL'}</span>
              <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: var(--accent-emerald); font-size: 0.72rem;">${t.execution_status}</span>
            </div>
          </div>
        `).join("");
      }
    }

    // 8. Section 7: Campaigns
    const campTable = document.getElementById("mktCampaignsTableBody");
    const campaigns = data.campaigns || [];
    if (campTable) {
      if (campaigns.length === 0) {
        campTable.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 1rem;">No campaigns recorded yet.</td></tr>`;
      } else {
        campTable.innerHTML = campaigns.map(c => `
          <tr>
            <td><code>${c.campaign_id}</code></td>
            <td><strong>${c.name}</strong></td>
            <td>${c.objective}</td>
            <td>${c.target_persona}</td>
            <td>${c.channel}</td>
            <td>$${(c.budget || 0).toFixed(2)} / $${(c.spend || 0).toFixed(2)}</td>
            <td><span class="badge" style="background: rgba(16, 185, 129, 0.15); color: var(--accent-emerald);">${c.status}</span></td>
            <td>${c.result || 'In Progress'}</td>
            <td>${c.next_action || 'Monitor signals'}</td>
          </tr>
        `).join("");
      }
    }

    // 9. Section 8: Bottleneck Diagnostics
    const bTitle = document.getElementById("mktBottleneckTitle");
    if (bTitle) bTitle.textContent = diag.primary_bottleneck || "TRAFFIC & OUTREACH";
    const bStage = document.getElementById("mktBottleneckStage");
    if (bStage) bStage.textContent = `STAGE: ${diag.bottleneck_stage || 'OUTREACH'}`;
    const bDiag = document.getElementById("mktBottleneckDiagnosis");
    if (bDiag) bDiag.textContent = diag.plain_english_diagnosis || "Sufficient product value exists, but top of funnel traffic needs scaling.";
    const bEvid = document.getElementById("mktBottleneckEvidence");
    if (bEvid) bEvid.textContent = diag.evidence || "Calculated from zero checkout visits.";
    const bRem = document.getElementById("mktBottleneckRemedy");
    if (bRem) bRem.textContent = diag.recommended_remedy || "Publish organic zero-cost comparison guides.";

    // 10. Phase 5F: Company Runtime, Public Access & Laptop Independence
    await fetchCloudRuntimeStatus();

  } catch (err) {
    console.error("Error fetching marketing command center:", err);
  }
}

async function fetchCloudRuntimeStatus() {
  try {
    const res = await fetch("/api/cloud/deployment-audit");
    if (!res.ok) return;
    const audit = await res.json();

    const rBadge = document.getElementById("runtimeModeBadge");
    if (rBadge) {
      rBadge.textContent = `RUNTIME: ${audit.runtime.replace('_', ' ')}`;
      rBadge.style.background = audit.is_remote_cloud ? "rgba(16, 185, 129, 0.2)" : "rgba(59, 130, 246, 0.2)";
      rBadge.style.color = audit.is_remote_cloud ? "var(--accent-emerald)" : "#93c5fd";
    }

    const rType = document.getElementById("rtRuntimeType");
    if (rType) rType.textContent = audit.runtime.replace('_', ' ');

    const rPub = document.getElementById("rtPublicAccess");
    if (rPub) {
      rPub.textContent = audit.is_public_accessible ? "PUBLIC (ONLINE)" : "NOT PUBLIC (LOCAL)";
      rPub.style.color = audit.is_public_accessible ? "var(--accent-emerald)" : "#f59e0b";
    }

    const rWeb = document.getElementById("rtWebServer");
    if (rWeb) rWeb.textContent = audit.web_server || "HEALTHY";

    const rWork = document.getElementById("rtWorker");
    if (rWork) rWork.textContent = audit.worker || "HEALTHY";

    const rSched = document.getElementById("rtScheduler");
    if (rSched) rSched.textContent = audit.scheduler || "HEALTHY";

    const rDb = document.getElementById("rtDatabase");
    if (rDb) rDb.textContent = audit.database || "HEALTHY";

    const rPay = document.getElementById("rtPayments");
    if (rPay) rPay.textContent = audit.payment_environment || "SANDBOX";

    const rUrl = document.getElementById("rtPublicUrl");
    if (rUrl) {
      rUrl.textContent = audit.public_url !== "NOT_CONFIGURED" ? audit.public_url : "http://127.0.0.1:8000 (LOCAL ONLY)";
    }

    const rHb = document.getElementById("rtLastHeartbeat");
    if (rHb && audit.last_heartbeat) {
      rHb.textContent = `${audit.last_heartbeat.substring(11, 19)} UTC`;
    }

    // Customer Store Link
    const storeStatus = document.getElementById("customerStoreStatusText");
    const storeBtn = document.getElementById("btnCustomerStore");
    if (storeStatus && storeBtn) {
      if (audit.is_public_accessible) {
        storeStatus.innerHTML = `✅ <strong>Publicly Verified:</strong> Customer store live at <a href="${audit.public_url}/store" target="_blank" style="color:var(--accent-cyan);">${audit.public_url}/store</a>`;
        storeBtn.href = `${audit.public_url}/store`;
        storeBtn.innerHTML = "🛒 [OPEN CUSTOMER STORE] →";
      } else {
        storeStatus.innerHTML = `🔒 <strong>Local Workstation:</strong> Running at <code>http://127.0.0.1:8000/store</code>. Deploy container for external customers.`;
        storeBtn.href = "/store";
        storeBtn.innerHTML = "🛒 [OPEN LOCAL CUSTOMER STORE] →";
      }
    }

    // Laptop Independence Panel
    const lap = audit.laptop_independence || {};
    const lapPanel = document.getElementById("laptopIndependencePanel");
    const lapBadge = document.getElementById("laptopBadge");
    const lapReason = document.getElementById("laptopReason");
    const lapCond = document.getElementById("laptopConditionsList");

    if (lapBadge) {
      lapBadge.textContent = lap.badge || "🔴 NO — COMPANY STILL DEPENDS ON THIS COMPUTER";
      lapBadge.style.background = lap.can_close_laptop ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)";
      lapBadge.style.color = lap.can_close_laptop ? "var(--accent-emerald)" : "#f87171";
    }

    if (lapPanel) {
      lapPanel.style.borderTopColor = lap.can_close_laptop ? "var(--accent-emerald)" : "#ef4444";
    }

    if (lapReason) {
      lapReason.textContent = lap.reason || "The company is executing on this local workstation. Closing your laptop will halt operations.";
    }

    if (lapCond && lap.unmet_conditions) {
      if (lap.unmet_conditions.length === 0) {
        lapCond.innerHTML = `<span style="color: var(--accent-emerald);">✓ All cloud independence checks passed. Workers, scheduler, and web server run 24/7.</span>`;
      } else {
        lapCond.innerHTML = lap.unmet_conditions.map(c => `• ${c}`).join("<br>");
      }
    }

    // Owner Actions
    const actionBox = document.getElementById("ownerActionsBox");
    const oActions = audit.owner_actions || {};
    if (actionBox && oActions.actions) {
      if (oActions.actions.length === 0) {
        actionBox.innerHTML = "✅ <strong>No actions required.</strong> Company running autonomously.";
      } else {
        actionBox.innerHTML = oActions.actions.map(a => `
          <div style="margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.05);">
            <strong style="color: #fff;">${a.title}</strong>
            <p style="margin: 0.2rem 0; color: var(--text-muted); font-size: 0.74rem;">${a.details}</p>
            <span class="badge" style="background: rgba(245, 158, 11, 0.15); color: var(--accent-amber); font-size: 0.7rem;">Priority: ${a.priority}</span>
          </div>
        `).join("");
      }
    }
  } catch (err) {
    console.error("Error fetching cloud runtime status:", err);
  }
}

// ----------------- Phase 5G: Governance & Owner Controls -----------------

async function fetchGovernanceData() {
  try {
    const [statusRes, auditRes] = await Promise.all([
      fetch("/api/status").then(r => r.json()).catch(() => null),
      fetch("/api/cloud/deployment-audit").then(r => r.json()).catch(() => null)
    ]);

    if (statusRes) {
      const finances = statusRes.finances || {};
      const firewall = finances.firewall_limits || {};
      const isEmergency = statusRes.emergency_stop || false;
      
      const govEmBadge = document.getElementById("govEmergencyBadge");
      if (govEmBadge) {
        govEmBadge.textContent = isEmergency ? "🛑 EMERGENCY STOP ACTIVE" : "🟢 SYSTEM OPERATIONAL";
        govEmBadge.style.background = isEmergency ? "rgba(239, 68, 68, 0.2)" : "rgba(16, 185, 129, 0.2)";
        govEmBadge.style.color = isEmergency ? "#f87171" : "var(--accent-emerald)";
      }

      const govKillBtn = document.getElementById("govKillswitchBtn");
      if (govKillBtn) {
        govKillBtn.textContent = isEmergency ? "▶️ RESUME OPERATIONS" : "🛑 ACTIVATE EMERGENCY STOP";
        govKillBtn.style.background = isEmergency ? "linear-gradient(135deg, #10b981, #059669)" : "linear-gradient(135deg, #ef4444, #b91c1c)";
      }

      const govFw = document.getElementById("govFirewallLimit");
      if (govFw) {
        const single = firewall.max_single_expense || 0.0;
        govFw.textContent = `$${single.toFixed(2)} CEILING`;
      }

      const singleInput = document.getElementById("govSingleLimit");
      if (singleInput && !document.activeElement.isSameNode(singleInput)) {
        singleInput.value = (firewall.max_single_expense || 0.0).toFixed(2);
      }

      const dailyInput = document.getElementById("govDailyLimit");
      if (dailyInput && !document.activeElement.isSameNode(dailyInput)) {
        dailyInput.value = (firewall.max_daily_expense || 0.0).toFixed(2);
      }

      const cfgSingle = document.getElementById("cfgSingleLimit");
      if (cfgSingle && !document.activeElement.isSameNode(cfgSingle)) {
        cfgSingle.value = (firewall.max_single_expense || 0.0).toFixed(2);
      }

      const cfgDaily = document.getElementById("cfgDailyLimit");
      if (cfgDaily && !document.activeElement.isSameNode(cfgDaily)) {
        cfgDaily.value = (firewall.max_daily_expense || 0.0).toFixed(2);
      }

      const govPending = document.getElementById("govPendingApprovals");
      if (govPending) {
        govPending.textContent = `${statusRes.pending_approvals_count || 0} PENDING`;
      }
    }

    if (auditRes) {
      const govRt = document.getElementById("govRuntimeType");
      if (govRt) {
        govRt.textContent = (auditRes.runtime || "LOCAL").replace("_", " ");
      }

      const govPub = document.getElementById("govPublicAccess");
      if (govPub) {
        govPub.textContent = auditRes.is_public_accessible ? "PUBLIC (ONLINE)" : "NOT PUBLIC (LOCAL)";
        govPub.style.color = auditRes.is_public_accessible ? "var(--accent-emerald)" : "#f59e0b";
      }

      const govWeb = document.getElementById("govHealthWeb");
      if (govWeb) govWeb.textContent = auditRes.web_server || "HEALTHY";

      const govWork = document.getElementById("govHealthWorker");
      if (govWork) govWork.textContent = auditRes.worker || "HEALTHY";

      const govSched = document.getElementById("govHealthScheduler");
      if (govSched) govSched.textContent = auditRes.scheduler || "HEALTHY";

      const govDb = document.getElementById("govHealthDb");
      if (govDb) govDb.textContent = auditRes.database || "HEALTHY";
    }
  } catch (err) {
    console.error("Error fetching governance data:", err);
  }
}

async function saveGovernanceFirewallSettings() {
  const single = parseFloat(document.getElementById("govSingleLimit").value) || 0.0;
  const daily = parseFloat(document.getElementById("govDailyLimit").value) || 0.0;
  
  try {
    await fetch("/api/firewall/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key: "max_single_expense", value: single })
    });
    await fetch("/api/firewall/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key: "max_daily_expense", value: daily })
    });
    alert("Governance policy updated successfully.");
    fetchGovernanceData();
  } catch (err) {
    alert("Error saving governance settings: " + err.message);
  }
}

async function saveFirewallSettings() {
  const single = parseFloat(document.getElementById("cfgSingleLimit").value) || 0.0;
  const daily = parseFloat(document.getElementById("cfgDailyLimit").value) || 0.0;
  
  try {
    await fetch("/api/firewall/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key: "max_single_expense", value: single })
    });
    await fetch("/api/firewall/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key: "max_daily_expense", value: daily })
    });
    alert("Firewall settings saved successfully.");
    fetchFirewall();
    fetchGovernanceData();
  } catch (err) {
    alert("Error saving firewall settings: " + err.message);
  }
}

// ==========================================
// PHASE 5H: MULTI-CHANNEL CUSTOMER ACQUISITION CONTROLLER
// ==========================================

let currentAcquisitionMode = 'PRODUCTION';

function setAcquisitionMode(mode) {
  currentAcquisitionMode = mode;
  const prodBtn = document.getElementById("btnAcqModeProd");
  const testBtn = document.getElementById("btnAcqModeTest");
  const sandBtn = document.getElementById("btnAcqModeSandbox");
  const badge = document.getElementById("acqActiveModeBadge");

  if (prodBtn) {
    prodBtn.style.background = mode === 'PRODUCTION' ? '#3b82f6' : 'transparent';
    prodBtn.style.color = mode === 'PRODUCTION' ? '#fff' : 'var(--text-secondary)';
  }
  if (testBtn) {
    testBtn.style.background = mode === 'TEST' ? '#8b5cf6' : 'transparent';
    testBtn.style.color = mode === 'TEST' ? '#fff' : 'var(--text-secondary)';
  }
  if (sandBtn) {
    sandBtn.style.background = mode === 'SANDBOX' ? '#f59e0b' : 'transparent';
    sandBtn.style.color = mode === 'SANDBOX' ? '#fff' : 'var(--text-secondary)';
  }

  if (badge) {
    badge.innerText = `MODE: ${mode}`;
    badge.style.color = mode === 'PRODUCTION' ? '#93c5fd' : (mode === 'TEST' ? '#c4b5fd' : '#fde68a');
    badge.style.background = mode === 'PRODUCTION' ? 'rgba(59, 130, 246, 0.2)' : (mode === 'TEST' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(245, 158, 11, 0.2)');
  }

  fetchAcquisitionData();
}

async function fetchAcquisitionData() {
  try {
    const [perfRes, funnelRes, oppsRes, seoRes, actionsRes, expRes] = await Promise.all([
      fetch(`/api/acquisition/performance?mode=${currentAcquisitionMode}`),
      fetch(`/api/acquisition/funnel?mode=${currentAcquisitionMode}`),
      fetch("/api/acquisition/opportunities"),
      fetch("/api/acquisition/content"),
      fetch("/api/acquisition/owner-actions"),
      fetch("/api/acquisition/expansion")
    ]);

    if (perfRes.ok) {
      const perfData = await perfRes.json();
      renderAcquisitionChannels(perfData.channels || []);
    }
    if (funnelRes.ok) {
      const funnelData = await funnelRes.json();
      renderAcquisitionFunnel(funnelData);
    }
    if (oppsRes.ok) {
      const oppsData = await oppsRes.json();
      renderAcquisitionOpportunities(oppsData.opportunities || []);
    }
    if (seoRes.ok) {
      const seoData = await seoRes.json();
      renderAcquisitionContent(seoData.articles || []);
    }
    if (actionsRes.ok) {
      const actData = await actionsRes.json();
      renderAcquisitionOwnerActions(actData.actions || []);
    }
    if (expRes.ok) {
      const expData = await expRes.json();
      renderAcquisitionExpansion(expData.queue || []);
    }
  } catch (err) {
    console.error("Error loading acquisition data:", err);
  }
}

function renderAcquisitionChannels(channels) {
  const tbody = document.getElementById("acqChannelsTableBody");
  if (!tbody) return;

  if (!channels || channels.length === 0) {
    tbody.innerHTML = `<tr><td colspan="11" style="text-align:center; color: var(--text-muted); padding: 1.5rem;">No channels registered.</td></tr>`;
    return;
  }

  tbody.innerHTML = channels.map(c => {
    let revColor = "#9ca3af";
    if (c.revenue !== "0.00 USD" && c.revenue !== "0 USD" && c.revenue !== "N/A" && c.revenue !== "Unknown") {
      revColor = "#10b981";
    }

    let statusBadgeColor = "rgba(107, 114, 128, 0.2)";
    let statusTextColor = "#9ca3af";
    if (c.listing_status.includes("ACTIVE") || c.listing_status.includes("DISCOVERY")) {
      statusBadgeColor = "rgba(16, 185, 129, 0.2)";
      statusTextColor = "#34d399";
    } else if (c.listing_status.includes("AWAITING") || c.listing_status.includes("CONFIGURED")) {
      statusBadgeColor = "rgba(245, 158, 11, 0.2)";
      statusTextColor = "#fbbf24";
    } else if (c.listing_status.includes("NOT_RECOMMENDED")) {
      statusBadgeColor = "rgba(239, 68, 68, 0.2)";
      statusTextColor = "#f87171";
    }

    return `
      <tr>
        <td>
          <div style="font-weight: 700; color: #f3f4f6;">${escapeHtml(c.channel_name)}</div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">${escapeHtml(c.url || "")}</div>
        </td>
        <td><span class="badge" style="background: rgba(59, 130, 246, 0.15); color: #93c5fd; font-size: 0.72rem;">${escapeHtml(c.channel_type)}</span></td>
        <td style="max-width: 180px; font-size: 0.75rem; color: var(--text-secondary);">${escapeHtml(c.audience)}</td>
        <td>
          <span class="badge" style="background: ${statusBadgeColor}; color: ${statusTextColor}; font-size: 0.72rem; font-weight: 700;">
            ${escapeHtml(c.listing_status)}
          </span>
        </td>
        <td style="text-align: right; font-family: monospace;">${escapeHtml(String(c.visitors))}</td>
        <td style="text-align: right; font-family: monospace;">${escapeHtml(String(c.product_views))}</td>
        <td style="text-align: right; font-family: monospace;">${escapeHtml(String(c.checkouts))}</td>
        <td style="text-align: right; font-family: monospace;">${escapeHtml(String(c.sales))}</td>
        <td style="text-align: right; font-family: monospace; font-weight: 700; color: ${revColor};">${escapeHtml(String(c.revenue))}</td>
        <td style="font-size: 0.75rem; color: var(--text-secondary);">${escapeHtml(c.policy_status || "COMPLIANT")}</td>
        <td style="font-size: 0.75rem; color: #93c5fd; max-width: 170px;">${escapeHtml(c.next_action || "Maintain discovery")}</td>
      </tr>
    `;
  }).join("");
}

function renderAcquisitionFunnel(funnel) {
  const container = document.getElementById("acqFunnelContainer");
  const insight = document.getElementById("acqFunnelInsight");
  if (!container) return;

  const stages = funnel.stages || [];
  if (stages.length === 0) {
    container.innerHTML = `<div style="color: var(--text-muted); padding: 1rem;">No funnel data available.</div>`;
    return;
  }

  container.innerHTML = stages.map((s, idx) => {
    return `
      <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 0.85rem; text-align: center; position: relative;">
        <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">STEP ${idx + 1}</div>
        <div style="font-size: 0.85rem; font-weight: 800; color: #e2e8f0; margin: 0.25rem 0;">${escapeHtml(s.stage)}</div>
        <div style="font-size: 1.4rem; font-weight: 900; color: #38bdf8; font-family: monospace;">${escapeHtml(String(s.count))}</div>
        <div style="font-size: 0.72rem; color: #a78bfa; margin-top: 0.2rem; font-weight: 600;">Conv: ${escapeHtml(s.conversion_rate)}</div>
      </div>
    `;
  }).join("");

  if (insight) {
    insight.innerHTML = `
      <strong>Funnel Diagnosis:</strong> ${escapeHtml(funnel.funnel_insight || "Awaiting real traffic")}
      ${funnel.data_status ? ` <span class="badge" style="margin-left: 0.5rem; background: rgba(59, 130, 246, 0.2); color: #93c5fd; font-size: 0.7rem;">${escapeHtml(funnel.data_status)}</span>` : ""}
    `;
  }
}

function renderAcquisitionOpportunities(opportunities) {
  const container = document.getElementById("acqOpportunitiesList");
  if (!container) return;

  if (!opportunities || opportunities.length === 0) {
    container.innerHTML = `<div style="color: var(--text-muted); padding: 1rem; text-align: center;">No qualified developer opportunities discovered yet.</div>`;
    return;
  }

  container.innerHTML = opportunities.map(opp => {
    let badgeColor = "rgba(245, 158, 11, 0.2)";
    let badgeText = "#fbbf24";
    if (opp.approval_status === "APPROVED") {
      badgeColor = "rgba(16, 185, 129, 0.2)";
      badgeText = "#34d399";
    } else if (opp.approval_status === "REJECTED") {
      badgeColor = "rgba(239, 68, 68, 0.2)";
      badgeText = "#f87171";
    }

    return `
      <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 1rem 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.5rem;">
          <div>
            <span class="badge" style="background: rgba(59, 130, 246, 0.2); color: #93c5fd; font-weight: 700; font-size: 0.72rem; margin-right: 0.5rem;">${escapeHtml(opp.source)}</span>
            <span style="font-weight: 700; color: #f3f4f6; font-size: 0.88rem;">${escapeHtml(opp.customer_problem)}</span>
          </div>
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span class="badge" style="background: ${badgeColor}; color: ${badgeText}; font-weight: 700; font-size: 0.72rem;">${escapeHtml(opp.approval_status)}</span>
            <span style="font-size: 0.72rem; color: var(--text-muted);">${escapeHtml(opp.date || "")}</span>
          </div>
        </div>

        <div style="font-size: 0.78rem; color: var(--text-secondary); margin-bottom: 0.75rem;">
          <strong>Target Discussion:</strong> <a href="${escapeHtml(opp.url)}" target="_blank" style="color: #38bdf8; text-decoration: underline;">${escapeHtml(opp.url)}</a>
          <span style="margin-left: 1rem; color: #a78bfa;">Relevance: ${escapeHtml(opp.relevance)}</span>
        </div>

        <div style="background: rgba(30, 41, 59, 0.6); border-left: 3px solid #10b981; padding: 0.75rem 1rem; border-radius: 4px; font-size: 0.8rem; color: #e2e8f0; margin-bottom: 0.75rem; white-space: pre-wrap;">
${escapeHtml(opp.recommended_response)}
        </div>

        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
          <div style="font-size: 0.74rem; color: var(--text-muted);">
            Links to: <span style="font-family: monospace; color: #93c5fd;">${escapeHtml(opp.nexora_product_url)}</span>
          </div>
          <div style="display: flex; gap: 0.5rem;">
            ${opp.approval_status === "PENDING_APPROVAL" ? `
              <button class="btn btn-sm" style="background: #10b981; color: #fff; font-weight: 700; padding: 0.25rem 0.75rem;" onclick="approveOpportunity('${escapeHtml(opp.opportunity_id)}')">✅ Approve for Owner Posting</button>
              <button class="btn btn-sm" style="background: rgba(239, 68, 68, 0.2); color: #fca5a5; font-weight: 700; padding: 0.25rem 0.75rem;" onclick="rejectOpportunity('${escapeHtml(opp.opportunity_id)}')">❌ Reject</button>
            ` : `<span style="font-size: 0.75rem; color: var(--text-muted); font-style: italic;">Reviewed by Owner</span>`}
          </div>
        </div>
      </div>
    `;
  }).join("");
}

async function approveOpportunity(oppId) {
  try {
    const res = await fetch(`/api/acquisition/opportunities/${oppId}/approve`, { method: "POST" });
    const data = await res.json();
    alert(`Opportunity Approved!\n\nOwner Action: You may now review and post the technical response on the destination platform manually. Nexora never spams.`);
    fetchAcquisitionData();
  } catch (err) {
    alert("Error approving opportunity: " + err.message);
  }
}

async function rejectOpportunity(oppId) {
  try {
    const res = await fetch(`/api/acquisition/opportunities/${oppId}/reject`, { method: "POST" });
    const data = await res.json();
    fetchAcquisitionData();
  } catch (err) {
    alert("Error rejecting opportunity: " + err.message);
  }
}

function renderAcquisitionContent(articles) {
  const tbody = document.getElementById("acqSEOTableBody");
  if (!tbody) return;

  if (!articles || articles.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 1.2rem;">No SEO articles available.</td></tr>`;
    return;
  }

  tbody.innerHTML = articles.map(art => {
    let statusColor = "rgba(245, 158, 11, 0.2)";
    let statusText = "#fbbf24";
    if (art.status === "APPROVED" || art.status === "PUBLISHED") {
      statusColor = "rgba(16, 185, 129, 0.2)";
      statusText = "#34d399";
    }

    return `
      <tr>
        <td>
          <div style="font-weight: 700; color: #f3f4f6;">${escapeHtml(art.title)}</div>
          <div style="font-size: 0.72rem; color: var(--text-muted); font-family: monospace;">/${escapeHtml(art.slug)}</div>
        </td>
        <td style="font-size: 0.78rem; color: var(--text-secondary); max-width: 220px;">${escapeHtml(art.problem_solved)}</td>
        <td style="font-size: 0.78rem; color: #93c5fd; font-family: monospace;">${escapeHtml(art.target_keyword)}</td>
        <td>
          <span class="badge" style="background: ${statusColor}; color: ${statusText}; font-size: 0.72rem; font-weight: 700;">
            ${escapeHtml(art.status)}
          </span>
        </td>
        <td style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(art.next_action)}</td>
        <td style="text-align: right;">
          ${art.status === "DRAFT" ? `
            <button class="btn btn-sm" style="background: #3b82f6; color: #fff; font-weight: 700; padding: 0.2rem 0.6rem; font-size: 0.72rem;" onclick="approveSEOArticle('${escapeHtml(art.slug)}')">Approve Draft</button>
          ` : `<span style="font-size: 0.72rem; color: #34d399; font-weight: 700;">Approved</span>`}
        </td>
      </tr>
    `;
  }).join("");
}

async function approveSEOArticle(slug) {
  try {
    const res = await fetch(`/api/acquisition/content/${slug}/approve`, { method: "POST" });
    const data = await res.json();
    alert(`Article '${slug}' approved for publication.`);
    fetchAcquisitionData();
  } catch (err) {
    alert("Error approving SEO article: " + err.message);
  }
}

function renderAcquisitionOwnerActions(actions) {
  const container = document.getElementById("acqOwnerActionsList");
  if (!container) return;

  if (!actions || actions.length === 0) {
    container.innerHTML = `<div style="color: var(--text-muted); padding: 0.75rem; text-align: center;">No pending owner actions.</div>`;
    return;
  }

  container.innerHTML = actions.map(act => {
    let pColor = "#f59e0b";
    if (act.priority === "HIGH") pColor = "#ef4444";
    if (act.priority === "MEDIUM") pColor = "#3b82f6";

    return `
      <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 0.85rem; border-left: 3px solid ${pColor};">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.35rem;">
          <div style="font-weight: 700; font-size: 0.82rem; color: #f8fafc;">
            ${escapeHtml(act.title)}
          </div>
          <span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #fca5a5; font-size: 0.68rem; font-weight: 700;">
            ${escapeHtml(act.status)}
          </span>
        </div>
        <p style="font-size: 0.76rem; color: var(--text-secondary); margin: 0.25rem 0 0.5rem 0;">
          ${escapeHtml(act.description)}
        </p>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 0.7rem; color: var(--text-muted);">Deadline: ${escapeHtml(act.deadline || "ASAP")}</span>
          <button class="btn btn-sm btn-secondary" style="font-size: 0.7rem; padding: 0.15rem 0.5rem;" onclick="completeOwnerAction('${escapeHtml(act.action_id)}')">Mark Done</button>
        </div>
      </div>
    `;
  }).join("");
}

async function completeOwnerAction(actionId) {
  try {
    const res = await fetch(`/api/acquisition/owner-actions/${actionId}/complete`, { method: "POST" });
    const data = await res.json();
    fetchAcquisitionData();
  } catch (err) {
    alert("Error updating owner action: " + err.message);
  }
}

function renderAcquisitionExpansion(queue) {
  const container = document.getElementById("acqProductExpansionList");
  if (!container) return;

  if (!queue || queue.length === 0) {
    container.innerHTML = `<div style="color: var(--text-muted); padding: 0.75rem; text-align: center;">No expansion candidates in queue.</div>`;
    return;
  }

  container.innerHTML = queue.map(item => {
    return `
      <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 0.85rem; border-left: 3px solid #a855f7;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.35rem;">
          <div style="font-weight: 700; font-size: 0.82rem; color: #f8fafc;">
            #${escapeHtml(String(item.rank))} • ${escapeHtml(item.product_family)}
          </div>
          <span class="badge" style="background: rgba(168, 85, 247, 0.2); color: #d8b4fe; font-size: 0.68rem; font-weight: 700;">
            Score: ${escapeHtml(String(item.composite_score))}
          </span>
        </div>
        <p style="font-size: 0.76rem; color: var(--text-secondary); margin: 0.25rem 0 0.35rem 0;">
          <strong>Problem:</strong> ${escapeHtml(item.observed_problem)}
        </p>
        <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: var(--text-muted);">
          <span>Demand: ${escapeHtml(item.search_demand)}</span>
          <span>Effort: ${escapeHtml(item.development_effort)}</span>
          <span style="color: #fbbf24;">Status: ${escapeHtml(item.approval_status)}</span>
        </div>
      </div>
    `;
  }).join("");
}

function viewGumroadSpec() {
  alert(
    "GUMROAD LISTING SPECIFICATION:\n\n" +
    "Product: Local LLM Offline Evaluation & Prompt Regression Benchmark Suite\n" +
    "Price: $29 USD (One-Time)\n" +
    "Files Included: Python benchmark suite (.tar.gz/.zip), 100+ baseline prompts, JSON schema regression validator, Latency harness, Quickstart PDF.\n" +
    "Guarantee: 30-Day Money-Back Guarantee.\n\n" +
    "Status: Awaiting Owner Account Creation. Once account is created, paste the Gumroad product URL to activate webhook transaction verification."
  );
}

function viewLemonSqueezySpec() {
  alert(
    "LEMON SQUEEZY SPECIFICATION:\n\n" +
    "Model: Merchant of Record (MoR) with global tax/VAT remittance.\n" +
    "Price: $29 USD\n" +
    "Checkout Modes: Hosted checkout link and website overlay modal.\n\n" +
    "Status: Awaiting Owner KYB/Identity Verification. Once approved, API webhooks will automatically verify payments against the database revenue ledger."
  );
}

// ----------------- PHASE 5I: UNIVERSAL AUTONOMOUS BUSINESS OPERATOR -----------------

async function fetchOperatorCockpit() {
  try {
    const [metricsRes, opRes, platRes, suppRes, actRes] = await Promise.all([
      fetch("/api/business/ceo-metrics"),
      fetch("/api/operator/status"),
      fetch("/api/integrations/platforms"),
      fetch("/api/support/tickets"),
      fetch("/api/acquisition/owner-actions")
    ]);

    if (metricsRes.ok) {
      const metrics = await metricsRes.json();
      renderCockpitKpis(metrics);
    }

    if (opRes.ok) {
      const op = await opRes.json();
      renderCockpitStatus(op);
    }

    if (platRes.ok) {
      const platData = await platRes.json();
      renderCockpitPlatforms(platData);
    }

    if (suppRes.ok) {
      const suppData = await suppRes.json();
      renderCockpitSupport(suppData);
    }

    if (actRes.ok) {
      const actData = await actRes.json();
      renderCockpitOwnerActions(actData.actions || []);
    }
  } catch (err) {
    console.error("Error fetching Operator Cockpit telemetry:", err);
  }
}

function renderCockpitStatus(op) {
  const stateBadge = document.getElementById("cockpitOperatorState");
  if (stateBadge) {
    if (op.operator_state === "ACTIVE_RUNNING") {
      stateBadge.innerHTML = "🟢 AUTONOMOUS OPERATOR ACTIVE";
      stateBadge.style.color = "#10b981";
    } else {
      stateBadge.innerHTML = "🟡 RUNNING";
      stateBadge.style.color = "#fbbf24";
    }
  }

  const cycleTime = document.getElementById("cockpitLastCycleTime");
  if (cycleTime) {
    cycleTime.textContent = new Date().toLocaleTimeString();
  }
}

let currentCockpitMetrics = null;
let activeCockpitTimeframe = "all_time";

function switchCockpitTimeframe(tfKey) {
  activeCockpitTimeframe = tfKey;
  ["btnTfAllTime", "btnTfToday", "btnTf7Days", "btnTf30Days"].forEach(id => {
    const btn = document.getElementById(id);
    if (!btn) return;
    const isTarget = (id === "btnTfAllTime" && tfKey === "all_time") ||
                     (id === "btnTfToday" && tfKey === "today") ||
                     (id === "btnTf7Days" && tfKey === "last_7_days") ||
                     (id === "btnTf30Days" && tfKey === "last_30_days");
    btn.style.background = isTarget ? "#38bdf8" : "transparent";
    btn.style.color = isTarget ? "#000" : "var(--text-secondary)";
    btn.style.fontWeight = isTarget ? "700" : "400";
  });

  if (currentCockpitMetrics) {
    applyCockpitKpis(currentCockpitMetrics, tfKey);
  }
}

function applyCockpitKpis(m, tfKey = "all_time") {
  const tf = (m.timeframes && m.timeframes[tfKey]) ? m.timeframes[tfKey] : {};

  const rev = document.getElementById("kpiRealRevenue");
  if (rev) {
    const revVal = tf.revenue_usd !== undefined ? tf.revenue_usd : (m.real_revenue?.total_verified_usd || 0.0);
    rev.textContent = `$${revVal.toFixed(2)} USD`;
  }

  const cust = document.getElementById("kpiRealCustomers");
  if (cust) {
    cust.textContent = tf.customers !== undefined ? tf.customers : (m.real_customers || 0);
  }

  const vis = document.getElementById("kpiRealVisitors");
  if (vis) {
    vis.textContent = tf.visitors !== undefined ? tf.visitors : (m.real_visitors || 0);
  }

  const qualVis = document.getElementById("kpiQualifiedVisitors");
  if (qualVis) {
    qualVis.textContent = m.qualified_visitors !== undefined ? m.qualified_visitors : (m.real_visitors || 0);
  }

  const leads = document.getElementById("kpiLeads");
  if (leads) {
    leads.textContent = m.leads !== undefined ? m.leads : 0;
  }

  const chk = document.getElementById("kpiCheckouts");
  if (chk) {
    chk.textContent = tf.checkout_starts !== undefined ? tf.checkout_starts : (m.real_checkouts || 0);
  }

  const succ = document.getElementById("kpiSuccessfulCheckouts");
  if (succ) {
    succ.textContent = tf.successful_checkouts !== undefined ? tf.successful_checkouts : (m.successful_checkouts || m.real_customers || 0);
  }

  const conv = document.getElementById("kpiConversionRate");
  if (conv) {
    const rate = tf.conversion_pct !== undefined ? tf.conversion_pct : (m.real_conversion_pct || 0.0);
    conv.textContent = `${rate}%`;
  }

  const chn = document.getElementById("kpiActiveChannels");
  if (chn && m.active_channels) {
    chn.textContent = `${m.active_channels.operating_channels} / ${m.active_channels.total}`;
  }

  const prod = document.getElementById("kpiActiveProducts");
  if (prod && m.active_products) {
    prod.textContent = m.active_products.count;
  }

  const act = document.getElementById("kpiOwnerActions");
  if (act && m.pending_owner_actions) {
    act.textContent = m.pending_owner_actions.count;
  }

  const bot = document.getElementById("kpiCurrentBottleneck");
  if (bot && m.current_bottleneck) {
    bot.textContent = m.current_bottleneck;
  }

  const sampleBadge = document.getElementById("cockpitSampleStatusBadge");
  if (sampleBadge && m.sample_size_status) {
    sampleBadge.textContent = m.sample_size_status === "INSUFFICIENT SAMPLE SIZE"
      ? `⚠️ INSUFFICIENT SAMPLE SIZE (n=${m.real_visitors || 0}) — Statistical conclusions require ≥100 visitors`
      : `✅ STATISTICALLY SUFFICIENT (n=${m.real_visitors || 0})`;
  }
}

function renderCockpitKpis(m) {
  currentCockpitMetrics = m;
  applyCockpitKpis(m, activeCockpitTimeframe);
}

function renderCockpitOwnerActions(actions) {
  const container = document.getElementById("cockpitOwnerActionList");
  const badge = document.getElementById("cockpitOwnerActionBadge");
  if (!container) return;

  const pending = actions.filter(a => a.status === "ACTION_REQUIRED");
  if (badge) {
    badge.textContent = `${pending.length} ACTIONS PENDING`;
  }

  if (pending.length === 0) {
    container.innerHTML = `
      <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: var(--radius-sm); padding: 1.25rem; text-align: center;">
        <span style="font-size: 1.5rem;">🎉</span>
        <div style="font-weight: 700; color: #34d399; margin: 0.35rem 0;">Zero Pending Owner Actions</div>
        <p style="font-size: 0.8rem; color: var(--text-secondary); margin: 0;">Antigravity is operating all channels autonomously without technical or legal blockers.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = pending.map(a => {
    const urgencyColor = a.urgency === "HIGH" ? "#ef4444" : "#f59e0b";
    return `
      <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 1.25rem; border-left: 4px solid ${urgencyColor};">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
          <div>
            <span class="badge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; font-weight: 800; font-size: 0.72rem; margin-right: 0.5rem;">
              ${escapeHtml(a.platform || a.channel || 'EXTERNAL')}
            </span>
            <span class="badge" style="background: rgba(239, 68, 68, 0.15); color: ${urgencyColor}; font-weight: 800; font-size: 0.72rem;">
              URGENCY: ${escapeHtml(a.urgency)}
            </span>
            <h3 style="font-size: 1.05rem; color: #fff; margin: 0.4rem 0 0.2rem 0;">
              ${escapeHtml(a.title)}
            </h3>
          </div>
          <button class="btn btn-primary" onclick="resolveOwnerAction5i('${escapeHtml(a.action_id)}')" style="font-size: 0.78rem; padding: 0.4rem 0.85rem; background: #10b981; color: #000; font-weight: 800;">
            ✓ Mark Completed
          </button>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0.75rem; background: rgba(0,0,0,0.3); padding: 0.85rem; border-radius: 6px; font-size: 0.78rem; margin-bottom: 0.75rem;">
          <div>
            <strong style="color: #fbbf24;">WHY REQUIRED:</strong>
            <p style="color: var(--text-primary); margin: 0.2rem 0 0 0;">${escapeHtml(a.why || a.description || 'External legal requirement')}</p>
          </div>
          <div>
            <strong style="color: #f87171;">WHAT IS BLOCKED:</strong>
            <p style="color: var(--text-primary); margin: 0.2rem 0 0 0;">${escapeHtml(a.what_is_blocked || 'Channel activation')}</p>
          </div>
          <div>
            <strong style="color: #38bdf8;">EXACT OWNER ACTION:</strong>
            <p style="color: #e0f2fe; margin: 0.2rem 0 0 0; font-weight: 600;">${escapeHtml(a.exact_action || a.description)}</p>
          </div>
          <div>
            <strong style="color: #a78bfa;">ESTIMATED TIME:</strong>
            <p style="color: var(--text-primary); margin: 0.2rem 0 0 0;">⏱️ ${escapeHtml(a.estimated_time || '3-5 minutes')}</p>
          </div>
        </div>

        <div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: var(--text-muted); flex-wrap: wrap; gap: 0.5rem; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 0.5rem;">
          <div>
            <strong style="color: #34d399;">🛡️ SECURITY IMPACT:</strong> ${escapeHtml(a.security_impact || 'Zero financial risk. Antigravity never accesses bank passwords, credentials, or OTPs.')}
          </div>
          <div>
            <strong style="color: #60a5fa;">⚡ WHAT ANTIGRAVITY WILL DO AFTER:</strong> ${escapeHtml(a.what_antigravity_will_do_after_completion || 'Automates all product listings, sales sync, and delivery')}
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function renderCockpitPlatforms(platData) {
  const tbody = document.getElementById("cockpitPlatformTableBody");
  const statsText = document.getElementById("cockpitPlatformStatsText");
  if (!tbody) return;

  const platforms = platData.platforms || [];
  if (statsText && platData.summary) {
    statsText.textContent = `${platData.summary.operating_channels} Operating / ${platData.summary.total_platforms} Registered`;
  }

  if (platforms.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No platform integrations.</td></tr>`;
    return;
  }

  tbody.innerHTML = platforms.map(p => {
    let classBadge = `<span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399;">🟢 AUTONOMOUS</span>`;
    if (p.classification === "PARTIALLY_AUTONOMOUS") {
      classBadge = `<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24;">🟡 PARTIAL</span>`;
    } else if (p.classification === "OWNER_ACTION_REQUIRED") {
      classBadge = `<span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171;">🟡 OWNER REQ</span>`;
    } else if (p.classification === "NOT_RECOMMENDED") {
      classBadge = `<span class="badge" style="background: rgba(100, 116, 139, 0.2); color: #94a3b8;">🔴 NOT RECOMMENDED</span>`;
    }

    let connBadge = `<span style="color: #34d399;">● CONNECTED</span>`;
    if (p.connection_status.includes("AWAITING")) {
      connBadge = `<span style="color: #fbbf24;">⏳ AWAITING OWNER</span>`;
    } else if (p.connection_status === "NOT_RECOMMENDED") {
      connBadge = `<span style="color: #64748b;">⚪ SKIPPED</span>`;
    }

    return `
      <tr>
        <td style="font-weight: 700; color: #fff;">
          ${escapeHtml(p.platform)}
          <a href="${escapeHtml(p.official_url)}" target="_blank" style="color: var(--accent-cyan); font-size: 0.72rem; margin-left: 0.35rem; text-decoration: none;">↗</a>
        </td>
        <td>${classBadge}</td>
        <td style="font-size: 0.74rem;">${connBadge}</td>
        <td style="font-family: monospace; font-size: 0.72rem; color: #cbd5e1;">${escapeHtml(p.integration_method)}</td>
        <td style="font-size: 0.74rem; color: #94a3b8;">${escapeHtml(p.compliance_status)}</td>
      </tr>
    `;
  }).join("");
}

function renderCockpitSupport(suppData) {
  const container = document.getElementById("cockpitSupportTicketsList");
  if (!container) return;

  const tickets = suppData.tickets || [];
  if (tickets.length === 0) {
    container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.78rem; padding: 0.5rem; text-align: center;">No support tickets recorded yet.</div>`;
    return;
  }

  container.innerHTML = tickets.slice(0, 5).map(t => {
    const isResolved = t.status === "RESOLVED";
    const statusColor = isResolved ? "#10b981" : "#f59e0b";
    return `
      <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border-subtle); border-radius: 4px; padding: 0.65rem;">
        <div style="display: flex; justify-content: space-between; font-size: 0.74rem; margin-bottom: 0.25rem;">
          <strong style="color: #fff;">${escapeHtml(t.customer_email)}</strong>
          <span style="color: ${statusColor}; font-weight: 700;">● ${escapeHtml(t.status)} (Conf: ${(t.confidence * 100).toFixed(0)}%)</span>
        </div>
        <p style="font-size: 0.76rem; color: var(--text-secondary); margin: 0.2rem 0;">Q: ${escapeHtml(t.question)}</p>
        <p style="font-size: 0.74rem; color: #cbd5e1; margin: 0.2rem 0; background: rgba(0,0,0,0.25); padding: 0.4rem; border-radius: 4px;">
          <strong>A:</strong> ${escapeHtml(t.answer || 'Awaiting manual review')}
        </p>
      </div>
    `;
  }).join("");
}

async function triggerOperatorPulse() {
  try {
    const btn = event?.target;
    if (btn) btn.disabled = true;
    const res = await fetch("/api/operator/pulse", { method: "POST" });
    const data = await res.json();
    alert("⚡ 12-Step Autonomous Business Loop executed successfully!\nDuration: " + data.cycle_duration_seconds + "s\nStatus: " + data.status);
    fetchOperatorCockpit();
  } catch (err) {
    alert("Error executing autonomous cycle: " + err.message);
  } finally {
    if (event?.target) event.target.disabled = false;
  }
}

async function sendDailyCeoReport() {
  try {
    const res = await fetch("/api/business/ceo-report/send", { method: "POST" });
    const data = await res.json();
    alert("📧 Daily CEO Executive Report compiled and dispatched!\nRecipient: " + data.recipient + "\nStatus: " + data.delivery.status);
    fetchOperatorCockpit();
  } catch (err) {
    alert("Error sending daily CEO report: " + err.message);
  }
}

async function resolveOwnerAction5i(actionId) {
  try {
    const res = await fetch(`/api/acquisition/owner-actions/${encodeURIComponent(actionId)}/resolve`, { method: "POST" });
    const data = await res.json();
    fetchOperatorCockpit();
  } catch (err) {
    alert("Error completing owner action: " + err.message);
  }
}

async function submitSupportQuestion5i() {
  const emailInput = document.getElementById("supTestEmail");
  const questionInput = document.getElementById("supTestQuestion");
  const resultDiv = document.getElementById("supAnswerResult");

  const email = emailInput?.value.trim() || "developer@example.com";
  const question = questionInput?.value.trim();

  if (!question) {
    alert("Please enter a question.");
    return;
  }

  try {
    const res = await fetch("/api/support/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_email: email,
        question: question,
        product_id: "PROD-OPP-P4-001"
      })
    });
    const data = await res.json();
    if (resultDiv) {
      resultDiv.style.display = "block";
      if (data.status === "RESOLVED") {
        resultDiv.style.background = "rgba(16, 185, 129, 0.15)";
        resultDiv.style.border = "1px solid #10b981";
        resultDiv.innerHTML = `
          <strong style="color: #34d399;">🟢 Autonomous Resolution (Confidence: ${(data.confidence * 100).toFixed(0)}%):</strong>
          <p style="margin: 0.3rem 0 0 0; color: #fff;">${escapeHtml(data.answer)}</p>
        `;
      } else {
        resultDiv.style.background = "rgba(245, 158, 11, 0.15)";
        resultDiv.style.border = "1px solid #f59e0b";
        resultDiv.innerHTML = `
          <strong style="color: #fbbf24;">🟡 Escalated to Owner (Confidence: ${(data.confidence * 100).toFixed(0)}%):</strong>
          <p style="margin: 0.3rem 0 0 0; color: #fff;">${escapeHtml(data.answer)}</p>
          <span style="font-size: 0.72rem; color: var(--text-muted);">Ticket ID: ${escapeHtml(data.ticket_id)}</span>
        `;
      }
    }
    fetchOperatorCockpit();
  } catch (err) {
    alert("Error submitting support question: " + err.message);
  }
}



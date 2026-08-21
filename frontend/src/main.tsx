import { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { ArrowRight, Boxes, ClipboardList, LayoutDashboard, LogOut, Users, Wrench } from 'lucide-react'
import './styles.css'
import './brand.css'
import { api, loadDashboardData, login, setAuthToken, type AuthUser } from './api'

type Role = 'student' | 'donor' | 'supervisor' | 'technician' | 'reviewer' | 'allocation_officer' | 'admin'
type DashboardData = Awaited<ReturnType<typeof loadDashboardData>>
type ApplicationRecord = { position?: number; name?: string; faculty?: string; programme?: string; status?: string }
type InventoryRecord = { asset?: string; model?: string; condition?: string; location?: string; status?: string }
type RefurbishmentRecord = { asset?: string; model?: string; technician?: string; completed?: string; result?: string }
type StudentRecord = { name?: string; number?: string; faculty?: string; programme?: string; device?: string }

const menus = [
  { label: 'Overview', icon: LayoutDashboard },
  { label: 'Applications', icon: ClipboardList },
  { label: 'Inventory', icon: Boxes },
  { label: 'Refurbishment', icon: Wrench },
  { label: 'Students', icon: Users },
]

function LoginView({ onLogin }: { onLogin: (user: AuthUser) => void }) {
  const [number, setNumber] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const submit = async () => {
    setBusy(true)
    setError('')
    try {
      onLogin(await login(number, password))
    } catch {
      setError('Invalid credentials or unavailable database.')
    } finally {
      setBusy(false)
    }
  }
  return <div className="landing-shell"><div className="landing-curve curve-blue"/><div className="landing-curve curve-red"/><div className="landing-curve curve-gold"/><div className="landing-logo"><img src="/brand/tut-logo.png" alt="Tshwane University of Technology"/></div><div className="landing-grid"><section className="landing-intro"><p className="landing-kicker">TUT DEVICE ACCESS PLATFORM</p><h1>EduConnect</h1><p>MISSING MIDDLE<br/>DEVICE PROGRAMME</p><small>Sign in to access your database-backed programme workspace.</small></section><section className="auth-card"><p className="auth-kicker">SECURE ACCESS</p><h2>Sign in to continue</h2><label>Student / Staff Number<div className="input-wrap"><input value={number} onChange={event => setNumber(event.target.value)} placeholder="Enter your number"/></div></label><label>Password<div className="input-wrap"><input value={password} onChange={event => setPassword(event.target.value)} type="password" placeholder="Enter your password" onKeyDown={event => { if (event.key === 'Enter') submit() }}/></div></label>{error && <p className="auth-error">{error}</p>}<button className="auth-primary" disabled={busy || !number || !password} onClick={submit}>{busy ? 'Signing in...' : 'Sign In'} <ArrowRight size={18}/></button><p className="auth-footer">New users must be registered by programme support.</p></section></div></div>
}

function EmptyState({ label }: { label: string }) {
  return <div className="empty-state"><strong>No {label} records</strong><span>Records created in PostgreSQL will appear here.</span></div>
}

function Table({ headers, rows, label }: { headers: string[]; rows: (string | number | undefined)[][]; label: string }) {
  if (!rows.length) return <EmptyState label={label}/>
  return <div className="table-wrap"><table><thead><tr>{headers.map(header => <th key={header}>{header}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell ?? ''}</td>)}</tr>)}</tbody></table></div>
}

function Dashboard({ user, onLogout }: { user: AuthUser; onLogout: () => void }) {
  const [section, setSection] = useState('Overview')
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    if (!['admin', 'allocation_officer', 'reviewer', 'supervisor', 'technician'].includes(user.role)) return
    loadDashboardData().then(setData).catch(() => setError('Unable to load records from PostgreSQL.'))
  }, [user.role])
  const overview = data?.overview
  const applications = (data?.applications ?? []) as ApplicationRecord[]
  const inventory = (data?.inventory ?? []) as InventoryRecord[]
  const refurbishment = (data?.refurbishment ?? []) as RefurbishmentRecord[]
  const students = (data?.students ?? []) as StudentRecord[]
  const activeRows = section === 'Applications' ? applications.map(item => [item.position, item.name, item.faculty, item.programme, item.status]) : section === 'Inventory' ? inventory.map(item => [item.asset, item.model, item.condition, item.location, item.status]) : section === 'Refurbishment' ? refurbishment.map(item => [item.asset, item.model, item.technician, item.completed, item.result]) : students.map(item => [item.name, item.number, item.faculty, item.programme, item.device])
  const headers = section === 'Applications' ? ['Queue', 'Student', 'Faculty', 'Programme', 'Status'] : section === 'Inventory' ? ['Asset', 'Model', 'Condition', 'Location', 'Status'] : section === 'Refurbishment' ? ['Asset', 'Model', 'Technician', 'Completed', 'Result'] : ['Student', 'Number', 'Faculty', 'Programme', 'Device']
  return <div className="app-shell"><aside className="sidebar"><div className="brand"><img src="/brand/tut-logo.png" alt="Tshwane University of Technology"/></div><nav>{menus.map(({ label, icon: Icon }) => <button className={section === label ? 'nav-item active' : 'nav-item'} key={label} onClick={() => setSection(label)}><Icon size={19}/><span>{label}</span></button>)}</nav><button className="user-card" onClick={onLogout}><span className="avatar">{user.name.slice(0, 2).toUpperCase()}</span><span><strong>{user.name}</strong><small>{user.role}</small></span><LogOut size={16}/></button></aside><main><header><div className="crumb">{user.name} <span>/</span> {section}</div><button className="secondary" onClick={onLogout}><LogOut size={16}/> Sign out</button></header><section className="content">{error && <div className="toast">{error}</div>}<div className="page-title"><div><p className="eyebrow">DATABASE-BACKED PROGRAMME</p><h1>{section}</h1><p>Live records from the EduConnect PostgreSQL database.</p></div></div>{section === 'Overview' ? <><div className="metrics"><Metric title="Applications" value={overview?.total_applications ?? 0}/><Metric title="Eligible students" value={overview?.eligible_students ?? 0}/><Metric title="Ready devices" value={overview?.ready_devices ?? 0}/><Metric title="Awaiting review" value={overview?.awaiting_review ?? 0}/></div><section className="panel"><h2>Programme data</h2><p>Metrics are calculated from records stored in PostgreSQL.</p></section></> : <section className="panel"><div className="panel-top"><div><h2>{section} records</h2><p>Only persisted database records are shown.</p></div></div><Table headers={headers} rows={activeRows} label={section.toLowerCase()}/></section>}</section></main></div>
}

function Metric({ title, value }: { title: string; value: number }) {
  return <article className="metric"><span className="metric-line blue"/><p>{title}</p><strong>{value}</strong><small>PostgreSQL records</small></article>
}

function App() {
  const [user, setUser] = useState<AuthUser | null>(null)
  if (!user) return <LoginView onLogin={setUser}/>
  return <Dashboard user={user} onLogout={() => { api.post('/auth/logout').catch(() => undefined); setAuthToken(null); setUser(null) }}/>
}

createRoot(document.getElementById('root')!).render(<App />)

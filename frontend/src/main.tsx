import { useEffect, useState, type FormEvent } from 'react'
import { createRoot } from 'react-dom/client'
import { ArrowRight, Boxes, ClipboardList, LayoutDashboard, LogOut, Users, Wrench } from 'lucide-react'
import './styles.css'
import './brand.css'
import { api, loadDashboardData, login, setAuthToken, type AuthUser } from './api'

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

const roleDashboardInfo: Record<string, { title: string; description: string; items: string[] }> = {
  student: { title: 'Student dashboard', description: 'Track your application, documents, and allocation status.', items: ['My application', 'Documents'] },
  donor: { title: 'Donor dashboard', description: 'Register donated devices and follow their progress through the programme.', items: ['My donations', 'Donate a device'] },
  supervisor: { title: 'Collection dashboard', description: 'Coordinate collections and account for every device handover.', items: ['Collections', 'Collection requests'] },
  technician: { title: 'Technical dashboard', description: 'Inspect, repair, and quality-check devices before allocation.', items: ['Work queue', 'Quality assurance'] },
}

function LoginView({ onLogin }: { onLogin: (user: AuthUser) => void }) {
  const [number, setNumber] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!number.trim() || !password) {
      setError('Enter your student or staff number and password.')
      return
    }
    setBusy(true)
    setError('')
    try {
      onLogin(await login(number.trim(), password))
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : 'Unable to sign in. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return <div className="landing-shell">
    <div className="landing-curve curve-blue" aria-hidden="true" />
    <div className="landing-curve curve-red" aria-hidden="true" />
    <div className="landing-curve curve-gold" aria-hidden="true" />
    <header className="landing-header"><a className="landing-logo" href="/" aria-label="EduConnect home"><img src="/brand/tut-logo.png" alt="Tshwane University of Technology" /></a></header>
    <div className="landing-grid">
      <section className="landing-intro" aria-labelledby="welcome-title">
        <p className="landing-kicker">TUT DEVICE ACCESS PLATFORM</p>
        <h1 id="welcome-title">EduConnect</h1>
        <p>MISSING MIDDLE<br />DEVICE PROGRAMME</p>
        <small>Secure access to the programme workspace for students, donors and TUT staff.</small>
      </section>
      <section className="auth-card" aria-labelledby="signin-title">
        <p className="auth-kicker">SECURE ACCESS</p>
        <h2 id="signin-title">Sign in to continue</h2>
        <form onSubmit={submit} noValidate>
          <label htmlFor="account-number">Student / Staff Number</label>
          <div className="input-wrap"><input id="account-number" name="number" value={number} onChange={event => setNumber(event.target.value)} autoComplete="username" placeholder="Enter your number" aria-invalid={Boolean(error)} /></div>
          <label htmlFor="account-password">Password</label>
          <div className="input-wrap"><input id="account-password" name="password" value={password} onChange={event => setPassword(event.target.value)} type="password" autoComplete="current-password" placeholder="Enter your password" aria-invalid={Boolean(error)} /></div>
          {error && <p className="auth-error" role="alert" aria-live="assertive">{error}</p>}
          <button className="auth-primary" type="submit" disabled={busy}>{busy ? 'Signing in...' : 'Sign in'} <ArrowRight size={18} aria-hidden="true" /></button>
        </form>
        <p className="auth-footer">New users must be registered by programme support.</p>
      </section>
    </div>
  </div>
}

function EmptyState({ label }: { label: string }) {
  return <div className="empty-state"><strong>No {label} records</strong><span>Records created in the local database will appear here.</span></div>
}

function Table({ headers, rows, label }: { headers: string[]; rows: (string | number | undefined)[][]; label: string }) {
  if (!rows.length) return <EmptyState label={label} />
  return <div className="table-wrap"><table><thead><tr>{headers.map(header => <th key={header}>{header}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell ?? ''}</td>)}</tr>)}</tbody></table></div>
}

function RoleDashboard({ user, onLogout }: { user: AuthUser; onLogout: () => void }) {
  const info = roleDashboardInfo[user.role] ?? roleDashboardInfo.student
  const [section, setSection] = useState(info.items[0])
  return <div className="app-shell"><aside className="sidebar"><div className="brand"><img src="/brand/tut-logo.png" alt="Tshwane University of Technology" /></div><nav aria-label="Primary navigation">{info.items.map(item => <button className={section === item ? 'nav-item active' : 'nav-item'} aria-current={section === item ? 'page' : undefined} key={item} onClick={() => setSection(item)}><LayoutDashboard size={19} aria-hidden="true" /><span>{item}</span></button>)}</nav><button className="user-card" onClick={onLogout}><span className="avatar" aria-hidden="true">{user.name.slice(0, 2).toUpperCase()}</span><span><strong>{user.name}</strong><small>{user.role}</small></span><LogOut size={16} aria-hidden="true" /><span className="sr-only">Sign out</span></button></aside><main><header><div className="crumb"><span>{user.name}</span> <span aria-hidden="true">/</span> <strong>{section}</strong></div><button className="secondary" onClick={onLogout}><LogOut size={16} aria-hidden="true" /> Sign out</button></header><section className="content"><div className="page-title"><div><p className="eyebrow">EDUCONNECT WORKSPACE</p><h1>{section}</h1><p>{info.description}</p></div></div><section className="panel role-home"><h2>{info.title}</h2><p>This workspace is ready for records associated with your account.</p><EmptyState label={section.toLowerCase()} /></section></section></main></div>
}

function Dashboard({ user, onLogout }: { user: AuthUser; onLogout: () => void }) {
  const [section, setSection] = useState('Overview')
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
	if (!['admin', 'allocation_officer', 'reviewer'].includes(user.role)) return
    loadDashboardData().then(setData).catch(() => setError('Unable to load records from PostgreSQL.'))
  }, [user.role])

  const overview = data?.overview
  const applications = (data?.applications ?? []) as ApplicationRecord[]
  const inventory = (data?.inventory ?? []) as InventoryRecord[]
  const refurbishment = (data?.refurbishment ?? []) as RefurbishmentRecord[]
  const students = (data?.students ?? []) as StudentRecord[]
  const activeRows = section === 'Applications' ? applications.map(item => [item.position, item.name, item.faculty, item.programme, item.status]) : section === 'Inventory' ? inventory.map(item => [item.asset, item.model, item.condition, item.location, item.status]) : section === 'Refurbishment' ? refurbishment.map(item => [item.asset, item.model, item.technician, item.completed, item.result]) : students.map(item => [item.name, item.number, item.faculty, item.programme, item.device])
  const headers = section === 'Applications' ? ['Queue', 'Student', 'Faculty', 'Programme', 'Status'] : section === 'Inventory' ? ['Asset', 'Model', 'Condition', 'Location', 'Status'] : section === 'Refurbishment' ? ['Asset', 'Model', 'Technician', 'Completed', 'Result'] : ['Student', 'Number', 'Faculty', 'Programme', 'Device']

  return <div className="app-shell"><aside className="sidebar"><div className="brand"><img src="/brand/tut-logo.png" alt="Tshwane University of Technology" /></div><nav aria-label="Primary navigation">{menus.map(({ label, icon: Icon }) => <button className={section === label ? 'nav-item active' : 'nav-item'} aria-current={section === label ? 'page' : undefined} key={label} onClick={() => setSection(label)}><Icon size={19} aria-hidden="true" /><span>{label}</span></button>)}</nav><button className="user-card" onClick={onLogout}><span className="avatar" aria-hidden="true">{user.name.slice(0, 2).toUpperCase()}</span><span><strong>{user.name}</strong><small>{user.role}</small></span><LogOut size={16} aria-hidden="true" /><span className="sr-only">Sign out</span></button></aside><main><header><div className="crumb"><span>{user.name}</span> <span aria-hidden="true">/</span> <strong>{section}</strong></div><button className="secondary" onClick={onLogout}><LogOut size={16} aria-hidden="true" /> Sign out</button></header><section className="content">{error && <div className="toast" role="alert">{error}</div>}<div className="page-title"><div><p className="eyebrow">DATABASE-BACKED PROGRAMME</p><h1>{section}</h1><p>Live records from the EduConnect local database.</p></div></div>{section === 'Overview' ? <><div className="metrics"><Metric title="Applications" value={overview?.total_applications ?? 0} /><Metric title="Eligible students" value={overview?.eligible_students ?? 0} /><Metric title="Ready devices" value={overview?.ready_devices ?? 0} /><Metric title="Awaiting review" value={overview?.awaiting_review ?? 0} /></div><section className="panel"><h2>Programme data</h2><p>Metrics are calculated from records stored in the local database.</p></section></> : <section className="panel"><div className="panel-top"><div><h2>{section} records</h2><p>Only persisted database records are shown.</p></div></div><Table headers={headers} rows={activeRows} label={section.toLowerCase()} /></section>}</section></main></div>
}

function Metric({ title, value }: { title: string; value: number }) {
  return <article className="metric"><span className="metric-line blue" /><p>{title}</p><strong>{value}</strong><small>PostgreSQL records</small></article>
}

function App() {
  const [user, setUser] = useState<AuthUser | null>(null)
  if (!user) return <LoginView onLogin={setUser} />
  const signOut = () => { api.post('/auth/logout').catch(() => undefined); setAuthToken(null); setUser(null) }
  const staffRoles = ['admin', 'allocation_officer', 'reviewer']
  return staffRoles.includes(user.role) ? <Dashboard user={user} onLogout={signOut} /> : <RoleDashboard user={user} onLogout={signOut} />
}

createRoot(document.getElementById('root')!).render(<App />)

import { useState, useEffect } from 'react'
import {
  LogIn, LogOut, Save, Plus, Trash2, Clock, Briefcase,
  Users, Tag, Menu, ChevronRight, Check, AlertCircle
} from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || ''

// Types
interface Hours {
  monday: string
  tuesday: string
  wednesday: string
  thursday: string
  friday: string
  saturday: string
  sunday: string
}

interface Service {
  id?: string
  title: string
  description: string
  price?: string
}

interface StaffMember {
  id?: string
  name: string
  role: string
  bio?: string
}

interface MenuItem {
  id?: string
  name: string
  description?: string
  price: string
  category?: string
}

interface Promotion {
  id?: string
  title: string
  description: string
  active: boolean
}

interface SiteContent {
  site_id: string
  business_name: string
  tagline?: string
  phone?: string
  email?: string
  address?: string
  hours: Hours
  services: Service[]
  staff: StaffMember[]
  menu_items: MenuItem[]
  promotions: Promotion[]
}

// Toast notification
function Toast({ message, type, onClose }: { message: string; type: 'success' | 'error'; onClose: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000)
    return () => clearTimeout(timer)
  }, [onClose])

  return (
    <div className={`fixed bottom-4 right-4 flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg ${
      type === 'success' ? 'bg-teal-600' : 'bg-red-600'
    }`}>
      {type === 'success' ? <Check className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
      {message}
    </div>
  )
}

// Login Screen
function LoginScreen({ onLogin }: { onLogin: (siteId: string, token: string) => void }) {
  const [siteId, setSiteId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ site_id: siteId, password })
      })

      if (!res.ok) {
        throw new Error('Invalid credentials')
      }

      const data = await res.json()
      localStorage.setItem('cms_site_id', data.site_id)
      localStorage.setItem('cms_token', data.token)
      onLogin(data.site_id, data.token)
    } catch {
      setError('Invalid site ID or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="card max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">Client CMS</h1>
          <p className="text-slate-400">Sign in to manage your website content</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Site ID</label>
            <input
              type="text"
              className="input"
              placeholder="e.g., clater-jewelers"
              value={siteId}
              onChange={(e) => setSiteId(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="label">Password</label>
            <input
              type="password"
              className="input"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {error && (
            <p className="text-red-400 text-sm">{error}</p>
          )}

          <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2" disabled={loading}>
            <LogIn className="w-4 h-4" />
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}

// Hours Editor
function HoursEditor({ hours, onChange }: { hours: Hours; onChange: (hours: Hours) => void }) {
  const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'] as const

  return (
    <div className="space-y-3">
      {days.map((day) => (
        <div key={day} className="flex items-center gap-4">
          <label className="w-24 text-sm font-medium capitalize text-slate-300">{day}</label>
          <input
            type="text"
            className="input flex-1"
            placeholder="e.g., 9am - 5pm or Closed"
            value={hours[day]}
            onChange={(e) => onChange({ ...hours, [day]: e.target.value })}
          />
        </div>
      ))}
    </div>
  )
}

// Services Editor
function ServicesEditor({ services, onChange }: { services: Service[]; onChange: (services: Service[]) => void }) {
  const addService = () => {
    onChange([...services, { title: '', description: '', price: '' }])
  }

  const updateService = (index: number, field: keyof Service, value: string) => {
    const updated = [...services]
    updated[index] = { ...updated[index], [field]: value }
    onChange(updated)
  }

  const removeService = (index: number) => {
    onChange(services.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-4">
      {services.map((service, index) => (
        <div key={index} className="bg-slate-700/50 rounded-lg p-4 space-y-3">
          <div className="flex justify-between items-start">
            <span className="text-sm text-slate-400">Service {index + 1}</span>
            <button onClick={() => removeService(index)} className="text-red-400 hover:text-red-300">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
          <input
            type="text"
            className="input"
            placeholder="Service title"
            value={service.title}
            onChange={(e) => updateService(index, 'title', e.target.value)}
          />
          <textarea
            className="input min-h-[80px]"
            placeholder="Description"
            value={service.description}
            onChange={(e) => updateService(index, 'description', e.target.value)}
          />
          <input
            type="text"
            className="input"
            placeholder="Price (optional)"
            value={service.price || ''}
            onChange={(e) => updateService(index, 'price', e.target.value)}
          />
        </div>
      ))}
      <button onClick={addService} className="btn-secondary flex items-center gap-2">
        <Plus className="w-4 h-4" /> Add Service
      </button>
    </div>
  )
}

// Menu Editor
function MenuEditor({ items, onChange }: { items: MenuItem[]; onChange: (items: MenuItem[]) => void }) {
  const addItem = () => {
    onChange([...items, { name: '', description: '', price: '', category: '' }])
  }

  const updateItem = (index: number, field: keyof MenuItem, value: string) => {
    const updated = [...items]
    updated[index] = { ...updated[index], [field]: value }
    onChange(updated)
  }

  const removeItem = (index: number) => {
    onChange(items.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-4">
      {items.map((item, index) => (
        <div key={index} className="bg-slate-700/50 rounded-lg p-4 space-y-3">
          <div className="flex justify-between items-start">
            <span className="text-sm text-slate-400">Item {index + 1}</span>
            <button onClick={() => removeItem(index)} className="text-red-400 hover:text-red-300">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input
              type="text"
              className="input"
              placeholder="Item name"
              value={item.name}
              onChange={(e) => updateItem(index, 'name', e.target.value)}
            />
            <input
              type="text"
              className="input"
              placeholder="Price"
              value={item.price}
              onChange={(e) => updateItem(index, 'price', e.target.value)}
            />
          </div>
          <input
            type="text"
            className="input"
            placeholder="Category (optional)"
            value={item.category || ''}
            onChange={(e) => updateItem(index, 'category', e.target.value)}
          />
          <input
            type="text"
            className="input"
            placeholder="Description (optional)"
            value={item.description || ''}
            onChange={(e) => updateItem(index, 'description', e.target.value)}
          />
        </div>
      ))}
      <button onClick={addItem} className="btn-secondary flex items-center gap-2">
        <Plus className="w-4 h-4" /> Add Menu Item
      </button>
    </div>
  )
}

// Staff Editor
function StaffEditor({ staff, onChange }: { staff: StaffMember[]; onChange: (staff: StaffMember[]) => void }) {
  const addMember = () => {
    onChange([...staff, { name: '', role: '', bio: '' }])
  }

  const updateMember = (index: number, field: keyof StaffMember, value: string) => {
    const updated = [...staff]
    updated[index] = { ...updated[index], [field]: value }
    onChange(updated)
  }

  const removeMember = (index: number) => {
    onChange(staff.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-4">
      {staff.map((member, index) => (
        <div key={index} className="bg-slate-700/50 rounded-lg p-4 space-y-3">
          <div className="flex justify-between items-start">
            <span className="text-sm text-slate-400">Team Member {index + 1}</span>
            <button onClick={() => removeMember(index)} className="text-red-400 hover:text-red-300">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input
              type="text"
              className="input"
              placeholder="Name"
              value={member.name}
              onChange={(e) => updateMember(index, 'name', e.target.value)}
            />
            <input
              type="text"
              className="input"
              placeholder="Role"
              value={member.role}
              onChange={(e) => updateMember(index, 'role', e.target.value)}
            />
          </div>
          <textarea
            className="input min-h-[80px]"
            placeholder="Bio (optional)"
            value={member.bio || ''}
            onChange={(e) => updateMember(index, 'bio', e.target.value)}
          />
        </div>
      ))}
      <button onClick={addMember} className="btn-secondary flex items-center gap-2">
        <Plus className="w-4 h-4" /> Add Team Member
      </button>
    </div>
  )
}

// Promotions Editor
function PromotionsEditor({ promotions, onChange }: { promotions: Promotion[]; onChange: (promos: Promotion[]) => void }) {
  const addPromo = () => {
    onChange([...promotions, { title: '', description: '', active: true }])
  }

  const updatePromo = (index: number, field: keyof Promotion, value: string | boolean) => {
    const updated = [...promotions]
    updated[index] = { ...updated[index], [field]: value }
    onChange(updated)
  }

  const removePromo = (index: number) => {
    onChange(promotions.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-4">
      {promotions.map((promo, index) => (
        <div key={index} className="bg-slate-700/50 rounded-lg p-4 space-y-3">
          <div className="flex justify-between items-start">
            <span className="text-sm text-slate-400">Promotion {index + 1}</span>
            <button onClick={() => removePromo(index)} className="text-red-400 hover:text-red-300">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
          <input
            type="text"
            className="input"
            placeholder="Promotion title"
            value={promo.title}
            onChange={(e) => updatePromo(index, 'title', e.target.value)}
          />
          <textarea
            className="input min-h-[80px]"
            placeholder="Description"
            value={promo.description}
            onChange={(e) => updatePromo(index, 'description', e.target.value)}
          />
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={promo.active}
              onChange={(e) => updatePromo(index, 'active', e.target.checked)}
              className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-teal-500 focus:ring-teal-500"
            />
            <span className="text-sm text-slate-300">Active</span>
          </label>
        </div>
      ))}
      <button onClick={addPromo} className="btn-secondary flex items-center gap-2">
        <Plus className="w-4 h-4" /> Add Promotion
      </button>
    </div>
  )
}

// Main Dashboard
function Dashboard({ siteId, token, onLogout }: { siteId: string; token: string; onLogout: () => void }) {
  const [content, setContent] = useState<SiteContent | null>(null)
  const [activeTab, setActiveTab] = useState('hours')
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  useEffect(() => {
    fetchContent()
  }, [siteId])

  const fetchContent = async () => {
    try {
      const res = await fetch(`${API_URL}/api/sites/${siteId}`)
      const data = await res.json()
      setContent(data)
    } catch (err) {
      console.error('Failed to fetch content:', err)
      setToast({ message: 'Failed to load content', type: 'error' })
    }
  }

  const saveContent = async () => {
    if (!content) return
    setSaving(true)

    try {
      const res = await fetch(`${API_URL}/api/admin/${siteId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Auth-Token': token
        },
        body: JSON.stringify(content)
      })

      if (!res.ok) throw new Error('Save failed')
      setToast({ message: 'Content saved successfully!', type: 'success' })
    } catch {
      setToast({ message: 'Failed to save content', type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  if (!content) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-slate-400">Loading...</div>
      </div>
    )
  }

  const tabs = [
    { id: 'hours', label: 'Hours', icon: Clock },
    { id: 'services', label: 'Services', icon: Briefcase },
    { id: 'menu', label: 'Menu', icon: Menu },
    { id: 'staff', label: 'Staff', icon: Users },
    { id: 'promotions', label: 'Promotions', icon: Tag },
  ]

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">{content.business_name}</h1>
            <p className="text-sm text-slate-400">{siteId}</p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={saveContent} className="btn-primary flex items-center gap-2" disabled={saving}>
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
            <button onClick={onLogout} className="btn-secondary flex items-center gap-2">
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto p-6">
        <div className="flex gap-6">
          {/* Sidebar */}
          <nav className="w-56 flex-shrink-0">
            <div className="card p-2 space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                    activeTab === tab.id
                      ? 'bg-teal-600 text-white'
                      : 'text-slate-400 hover:bg-slate-700 hover:text-white'
                  }`}
                >
                  <tab.icon className="w-5 h-5" />
                  {tab.label}
                  <ChevronRight className={`w-4 h-4 ml-auto transition-transform ${activeTab === tab.id ? 'rotate-90' : ''}`} />
                </button>
              ))}
            </div>
          </nav>

          {/* Content */}
          <main className="flex-1">
            <div className="card">
              {activeTab === 'hours' && (
                <>
                  <h2 className="text-lg font-semibold text-white mb-4">Business Hours</h2>
                  <HoursEditor
                    hours={content.hours}
                    onChange={(hours) => setContent({ ...content, hours })}
                  />
                </>
              )}

              {activeTab === 'services' && (
                <>
                  <h2 className="text-lg font-semibold text-white mb-4">Services</h2>
                  <ServicesEditor
                    services={content.services}
                    onChange={(services) => setContent({ ...content, services })}
                  />
                </>
              )}

              {activeTab === 'menu' && (
                <>
                  <h2 className="text-lg font-semibold text-white mb-4">Menu Items</h2>
                  <MenuEditor
                    items={content.menu_items}
                    onChange={(menu_items) => setContent({ ...content, menu_items })}
                  />
                </>
              )}

              {activeTab === 'staff' && (
                <>
                  <h2 className="text-lg font-semibold text-white mb-4">Team Members</h2>
                  <StaffEditor
                    staff={content.staff}
                    onChange={(staff) => setContent({ ...content, staff })}
                  />
                </>
              )}

              {activeTab === 'promotions' && (
                <>
                  <h2 className="text-lg font-semibold text-white mb-4">Promotions</h2>
                  <PromotionsEditor
                    promotions={content.promotions}
                    onChange={(promotions) => setContent({ ...content, promotions })}
                  />
                </>
              )}
            </div>
          </main>
        </div>
      </div>

      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}
    </div>
  )
}

// Main App
export default function App() {
  const [auth, setAuth] = useState<{ siteId: string; token: string } | null>(null)

  useEffect(() => {
    const siteId = localStorage.getItem('cms_site_id')
    const token = localStorage.getItem('cms_token')
    if (siteId && token) {
      setAuth({ siteId, token })
    }
  }, [])

  const handleLogin = (siteId: string, token: string) => {
    setAuth({ siteId, token })
  }

  const handleLogout = () => {
    localStorage.removeItem('cms_site_id')
    localStorage.removeItem('cms_token')
    setAuth(null)
  }

  if (!auth) {
    return <LoginScreen onLogin={handleLogin} />
  }

  return <Dashboard siteId={auth.siteId} token={auth.token} onLogout={handleLogout} />
}

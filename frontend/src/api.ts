import axios from 'axios'

/** Shared HTTP client for the FastAPI service. */
export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api' })

export type AuthUser = { id: number; number: string; name: string; role: string }

export function setAuthToken(token: string | null) {
	if (token) api.defaults.headers.common.Authorization = `Bearer ${token}`
	else delete api.defaults.headers.common.Authorization
}

export async function login(number: string, password: string) {
	const response = await api.post<{ access_token: string; user: AuthUser }>('/auth/login', { number, password })
	setAuthToken(response.data.access_token)
	return response.data.user
}

export async function loadDashboardData() {
	const [overview, applications, inventory, refurbishment, students] = await Promise.all([
		api.get('/overview'),
		api.get('/applications'),
		api.get('/inventory'),
		api.get('/refurbishment'),
		api.get('/students'),
	])
	return {
		overview: overview.data,
		applications: applications.data.items,
		inventory: inventory.data.items,
		refurbishment: refurbishment.data.items,
		students: students.data.items,
	}
}

export async function reviewApplication(id: string, decision: 'approve' | 'reject' | 'request_info', reason: string) {
	return api.post(`/applications/${id}/review`, { decision, reason })
}

export async function reserveDevice(applicationId: string, deviceAsset: string) {
	return api.post('/allocations/reserve', { application_id: applicationId, device_asset: deviceAsset })
}

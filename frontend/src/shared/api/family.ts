import { request } from './base'
import type { APIResponse } from './types'

export type UserRole = 'adult' | 'child'

export interface Family {
  id: number;
  name: string;
  invite_code: string;
  created_by: number;
  created_at: string;
}

export interface FamilyMember {
  id: number;
  name: string;
  role: UserRole | null;
  monthly_income: number | null;
  income_share: number | null;
}

export interface FamilyState {
  family: Family;
  members: FamilyMember[];
}

export interface CreateFamilyRequest {
  name: string;
}

export interface JoinFamilyRequest {
  invite_code: string;
}

export interface SetRoleRequest {
  role: UserRole;
  monthly_income?: number;
}

export function createFamily(
  data: CreateFamilyRequest,
): Promise<APIResponse<Family>> {
  return request<Family>('/family/create', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function joinFamily(
  data: JoinFamilyRequest,
): Promise<APIResponse<Family>> {
  return request<Family>('/family/join', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function setFamilyRole(
  data: SetRoleRequest,
): Promise<APIResponse<FamilyMember>> {
  return request<FamilyMember>('/family/role', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function getMyFamily(): Promise<APIResponse<FamilyState>> {
  return request<FamilyState>('/family/me', {
    method: 'GET',
  })
}

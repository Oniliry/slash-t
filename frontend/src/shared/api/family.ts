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
  is_admin: boolean;
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

export interface RenameFamilyRequest {
  name: string;
}

export interface UpdateMemberRequest {
  name?: string;
  monthly_income?: number;
}

export interface BudgetSplitRequest {
  member_a_id: number;
  member_b_id: number;
  member_a_ratio: number;
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

export function leaveFamily(): Promise<APIResponse<null>> {
  return request<null>('/family/leave', {
    method: 'POST',
  })
}

export function renameFamily(
  data: RenameFamilyRequest,
): Promise<APIResponse<Family>> {
  return request<Family>('/family/name', {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function updateFamilyMember(
  memberId: number,
  data: UpdateMemberRequest,
): Promise<APIResponse<FamilyState>> {
  return request<FamilyState>(`/family/members/${memberId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function removeFamilyMember(
  memberId: number,
): Promise<APIResponse<FamilyState>> {
  return request<FamilyState>(`/family/members/${memberId}`, {
    method: 'DELETE',
  })
}

export function updateBudgetSplit(
  data: BudgetSplitRequest,
): Promise<APIResponse<FamilyState>> {
  return request<FamilyState>('/family/budget-split', {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

import { request } from './base'
import type { APIResponse } from './types'

export type ExpenseOwnerType = 'self' | 'member' | 'shared'
export type DebtStatus = 'pending' | 'confirmed' | 'netted'
export type ExpenseCategory =
  | 'groceries'
  | 'utilities'
  | 'transport'
  | 'cafe'
  | 'entertainment'
  | 'health'
  | 'clothing'
  | 'other'

export interface DebtParticipant {
  id: number;
  name: string;
}

export interface Debt {
  id: number;
  expense_id: number;
  amount: number;
  status: DebtStatus;
  created_at: string;
  confirmed_at: string | null;
  debtor: DebtParticipant;
  creditor: DebtParticipant;
}

export interface Expense {
  id: number;
  amount: number;
  owner_type: ExpenseOwnerType;
  owner_id: number | null;
  payer_id: number;
  payer_name?: string | null;
  can_edit?: boolean;
  category: ExpenseCategory;
  created_at: string;
  debts: Debt[];
}

export interface MyDebts {
  i_owe: Debt[];
  owed_to_me: Debt[];
}

export interface CreateExpenseRequest {
  amount: number;
  owner_type: ExpenseOwnerType;
  owner_id?: number | null;
  category: ExpenseCategory;
}

export function createExpense(
  data: CreateExpenseRequest,
): Promise<APIResponse<Expense>> {
  return request<Expense>('/expenses', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateExpense(
  expenseId: number,
  data: CreateExpenseRequest,
): Promise<APIResponse<Expense>> {
  return request<Expense>(`/expenses/${expenseId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function getExpenses(limit = 50): Promise<APIResponse<Expense[]>> {
  return request<Expense[]>(`/expenses?limit=${limit}`, {
    method: 'GET',
  })
}

export function getMyDebts(): Promise<APIResponse<MyDebts>> {
  return request<MyDebts>('/debts/me', {
    method: 'GET',
  })
}

export function confirmDebt(debtId: number): Promise<APIResponse<Debt>> {
  return request<Debt>(`/debts/${debtId}/confirm`, {
    method: 'POST',
  })
}

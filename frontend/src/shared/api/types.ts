export interface APIResponse<T> {
  error: boolean;
  message: string | null;
  data: T | null;
  type: string | null;
}export interface APIResponse<T> {
    error: boolean;
    message: string | null;
    data: T | null;
    type: string | null;
}
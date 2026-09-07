import { useCallback, useEffect, useState } from "react";

import { getExpenses } from "../../../shared/api/expenses.ts";
import { getMyFamily } from "../../../shared/api/family.ts";
import AddPurchaseModal from "../../../widgets/AddPurchase/AddPurchaseModal.jsx";
import ExpenseSummary from "../sections/ExpenseSummary.jsx";
import ExpenseList from "../sections/ExpenseList.jsx";
import "./ExpensesPage.css";

function ExpensesPage() {
  const [expenses, setExpenses] = useState([]);
  const [members, setMembers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingExpense, setEditingExpense] = useState(null);

  const loadExpenses = useCallback(async () => {
    const response = await getExpenses();

    if (!response.error && response.data) {
      setExpenses(response.data);
      setError("");
    } else if (response.type !== "family_required") {
      setError(response.message ?? "Не удалось загрузить расходы.");
    }

    setIsLoading(false);
  }, []);

  const loadMembers = useCallback(async () => {
    const response = await getMyFamily();

    if (!response.error && response.data) {
      setMembers(response.data.members);
    }
  }, []);

  useEffect(() => {
    loadExpenses();
    loadMembers();

    // Обновляем списки сразу после добавления покупки через кнопку "+"
    window.addEventListener("slash-t:expense-created", loadExpenses);
    return () => window.removeEventListener("slash-t:expense-created", loadExpenses);
  }, [loadExpenses, loadMembers]);

  return (
    <section className="page">
      <header className="page__header">
        <div>
          <p className="page__eyebrow">Семейные финансы</p>
          <h1>Расходы</h1>
          <p className="page__lead">
            Просматривайте чеки и распределяйте траты по категориям.
          </p>
        </div>
      </header>
      <ExpenseSummary expenses={expenses} members={members} isLoading={isLoading} />
      <ExpenseList
        expenses={expenses}
        isLoading={isLoading}
        error={error}
        onEdit={setEditingExpense}
      />
      {editingExpense && (
        <AddPurchaseModal
          expense={editingExpense}
          onClose={() => setEditingExpense(null)}
          onCreated={() => {
            setEditingExpense(null);
            loadExpenses();
          }}
        />
      )}
    </section>
  );
}

export default ExpensesPage;

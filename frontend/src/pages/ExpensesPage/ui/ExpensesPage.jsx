import ExpenseSummary from '../sections/ExpenseSummary.jsx'
import ExpenseList from '../sections/ExpenseList.jsx'
import './ExpensesPage.css'

function ExpensesPage() {
  return <section className="page"><header className="page__header"><div><p className="page__eyebrow">Семейные финансы</p><h1>Расходы</h1><p className="page__lead">Просматривайте чеки и распределяйте траты по категориям.</p></div></header><ExpenseSummary /><ExpenseList /></section>
}

export default ExpensesPage
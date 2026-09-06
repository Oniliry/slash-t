import BudgetBar from './BudgetBar.jsx'

import './FamilyWidgets.css'

function formatMoney(value) {
  return `${new Intl.NumberFormat('ru-RU').format(value)} ₽`
}

function BudgetWidget({ members, isAdmin, onChanged }) {
  const totalIncome = members
    .filter((member) => member.role === 'adult')
    .reduce((sum, member) => sum + Number(member.monthly_income ?? 0), 0)

  return (
    <article className="family-widget budget-widget">
      <h2>Общий бюджет</h2>
      <p className="budget-widget__total">{formatMoney(totalIncome)}/мес</p>
      <BudgetBar members={members} isAdmin={isAdmin} onChanged={onChanged} />
    </article>
  )
}

export default BudgetWidget

<!-- ABOUTME: Restocking recommendations view with budget slider and order placement. -->
<!-- ABOUTME: Fetches recommended items to restock based on demand gap and available budget. -->
<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-card">
      <div class="budget-label">{{ t('restocking.budgetLabel') }}</div>
      <div class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
      <input
        type="range"
        class="budget-slider"
        :min="1"
        :max="50000"
        :step="500"
        v-model.number="budget"
      />
      <div class="budget-range-labels">
        <span>{{ currencySymbol }}0</span>
        <span>{{ currencySymbol }}50,000</span>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ (recommendations.total_cost || 0).toLocaleString() }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ (recommendations.remaining_budget || 0).toLocaleString() }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.itemsCount') }}</div>
          <div class="stat-value">{{ (recommendations.items || []).length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.title') }}</h3>
          <button
            class="btn-primary"
            :disabled="!(recommendations.items && recommendations.items.length) || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="orderPlaced" class="success-message">{{ t('restocking.orderPlaced') }}</div>
        <div v-if="orderError" class="error">{{ t('restocking.orderFailed') }}</div>

        <div v-if="!(recommendations.items && recommendations.items.length)" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.demandGap') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.lineCost') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations.items" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>{{ item.demand_gap }}</td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td>{{ item.quantity }}</td>
                <td><strong>{{ currencySymbol }}{{ item.line_cost.toLocaleString() }}</strong></td>
                <td>
                  <span :class="['badge', getLeadTimeBadgeClass(item.lead_time_days)]">
                    {{ t('restocking.leadTimeDays', { days: item.lead_time_days }) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const budget = ref(10000)
    const loading = ref(true)
    const error = ref(null)
    const recommendations = ref({ budget: 0, total_cost: 0, remaining_budget: 0, items: [] })
    const submitting = ref(false)
    const orderPlaced = ref(false)
    const orderError = ref(false)

    let debounceTimer = null

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        orderPlaced.value = false
        orderError.value = false
        recommendations.value = await api.getRestockingRecommendations(budget.value)
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const getLeadTimeBadgeClass = (days) => {
      if (days <= 4) return 'success'
      if (days <= 8) return 'warning'
      return 'danger'
    }

    const placeOrder = async () => {
      submitting.value = true
      orderPlaced.value = false
      orderError.value = false
      try {
        await api.submitRestockingOrder({
          budget: budget.value,
          items: recommendations.value.items.map(item => ({
            item_sku: item.item_sku,
            item_name: item.item_name,
            quantity: item.quantity,
            unit_cost: item.unit_cost,
            lead_time_days: item.lead_time_days
          }))
        })
        orderPlaced.value = true
        await loadRecommendations()
      } catch (err) {
        orderError.value = true
        console.error('Failed to place restocking order:', err)
      } finally {
        submitting.value = false
      }
    }

    watch(budget, () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 300)
    })

    onMounted(loadRecommendations)

    return {
      t,
      currencySymbol,
      budget,
      loading,
      error,
      recommendations,
      submitting,
      orderPlaced,
      orderError,
      getLeadTimeBadgeClass,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.5rem;
}

.budget-value {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  margin-bottom: 1rem;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  cursor: pointer;
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.375rem;
  font-size: 0.75rem;
  color: #94a3b8;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.success-message {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 2.5rem;
  color: #64748b;
  font-size: 0.938rem;
}
</style>

const { createApp, ref, reactive, computed } = Vue;

function formatNumber(n) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(n);
}

const App = {
  setup() {
    const loading = ref(false);
    const form = reactive({
      age: 30,
      sex: 'male',
      height_cm: 175,
      weight_kg: 70,
      activity_level: 'moderate',
      goal: 'lose',
      weekly_change_kg: 0.5,
      dietary_preference: 'balanced',
    });

    const response = ref(null);
    const error = ref(null);

    async function generatePlan() {
      loading.value = true;
      error.value = null;
      response.value = null;
      try {
        const res = await fetch('/api/plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(form),
        });
        const json = await res.json();
        if (!res.ok) throw new Error(json.error || 'Request failed');
        response.value = json;
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    }

    return { form, response, error, loading, generatePlan, formatNumber };
  },
  template: `
    <div class="topbar">
      <div class="brand">
        <div class="logo"></div>
        <div class="title">LeanPlan</div>
      </div>
    </div>

    <div class="content">
      <div class="card">
        <div class="form-grid">
          <div>
            <label>Age</label>
            <input type="number" v-model.number="form.age" min="14" max="90" />
          </div>
          <div>
            <label>Sex</label>
            <select v-model="form.sex">
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
          </div>
          <div>
            <label>Height (cm)</label>
            <input type="number" v-model.number="form.height_cm" min="120" max="230" />
          </div>
          <div>
            <label>Weight (kg)</label>
            <input type="number" v-model.number="form.weight_kg" min="35" max="250" />
          </div>
          <div>
            <label>Activity Level</label>
            <select v-model="form.activity_level">
              <option value="sedentary">Sedentary</option>
              <option value="light">Light</option>
              <option value="moderate">Moderate</option>
              <option value="active">Active</option>
              <option value="very_active">Very Active</option>
            </select>
          </div>
          <div>
            <label>Goal</label>
            <select v-model="form.goal">
              <option value="lose">Lose</option>
              <option value="maintain">Maintain</option>
              <option value="gain">Gain</option>
            </select>
          </div>
          <div>
            <label>Weekly Change (kg)</label>
            <input type="number" v-model.number="form.weekly_change_kg" step="0.1" min="0.1" max="1.2" />
          </div>
          <div>
            <label>Diet Preference</label>
            <select v-model="form.dietary_preference">
              <option value="balanced">Balanced</option>
              <option value="high_protein">High Protein</option>
              <option value="low_carb">Low Carb</option>
              <option value="keto">Keto</option>
              <option value="vegetarian">Vegetarian</option>
              <option value="vegan">Vegan</option>
            </select>
          </div>
        </div>

        <div class="generate">
          <button class="btn" :disabled="loading" @click="generatePlan">{{ loading ? 'Generating…' : 'Generate Plan' }}</button>
          <span class="hint">OpenAI-like minimal UI</span>
        </div>
      </div>

      <div class="chat">
        <div v-if="!response && !error" class="message">
          <div class="avatar"></div>
          <div class="bubble">
            <h3>Welcome to LeanPlan</h3>
            <div>Enter your details to generate a personalized daily and weekly plan.</div>
          </div>
        </div>

        <div v-if="error" class="message">
          <div class="avatar"></div>
          <div class="bubble">
            <h3 style="color: var(--danger)">Error</h3>
            <div>{{ error }}</div>
          </div>
        </div>

        <div v-if="response" class="message">
          <div class="avatar"></div>
          <div class="bubble">
            <h3>Your Plan</h3>
            <div class="kpi">
              <div class="item">BMR<strong>{{ formatNumber(response.metrics.bmr) }}</strong></div>
              <div class="item">TDEE<strong>{{ formatNumber(response.metrics.tdee) }}</strong></div>
              <div class="item">Target kcal<strong>{{ formatNumber(response.metrics.target_calories) }}</strong></div>
            </div>

            <div class="kpi">
              <div class="item">Protein (g)<strong>{{ response.daily_plan.macros.protein_g }}</strong></div>
              <div class="item">Fat (g)<strong>{{ response.daily_plan.macros.fat_g }}</strong></div>
              <div class="item">Carbs (g)<strong>{{ response.daily_plan.macros.carbs_g }}</strong></div>
            </div>

            <div class="meals">
              <div class="item"><span>Breakfast</span><strong>{{ response.daily_plan.meals.breakfast }} kcal</strong></div>
              <div class="item"><span>Lunch</span><strong>{{ response.daily_plan.meals.lunch }} kcal</strong></div>
              <div class="item"><span>Snack</span><strong>{{ response.daily_plan.meals.snack }} kcal</strong></div>
              <div class="item"><span>Dinner</span><strong>{{ response.daily_plan.meals.dinner }} kcal</strong></div>
            </div>

            <div style="margin-top: 8px; color: var(--muted); font-size: 12px">
              Steps target: <strong style="color: var(--text)">{{ response.daily_plan.steps_target }}</strong> · Water: <strong style="color: var(--text)">{{ response.daily_plan.water_liters }} L</strong>
            </div>

            <ul style="margin-top: 8px; color: var(--muted);">
              <li v-for="(n, i) in response.daily_plan.notes" :key="i">{{ n }}</li>
            </ul>

            <div class="card" style="margin-top: 12px;">
              <div style="font-weight: 600; margin-bottom: 6px;">Weekly Overview</div>
              <div style="display:grid; grid-template-columns: repeat(7,1fr); gap: 8px;">
                <div v-for="d in response.week_plan.days" :key="d.day" class="kpi item" style="text-align:center">
                  <div style="font-size:12px; color: var(--muted)">Day {{ d.day }}</div>
                  <div style="font-size:14px; color: var(--text)">{{ formatNumber(d.calories) }} kcal</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="footer">
      <div class="hint">This is a demo health planner. Not medical advice.</div>
    </div>
  `,
};

createApp(App).mount('#app');


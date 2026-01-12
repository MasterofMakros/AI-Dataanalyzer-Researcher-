<template>
  <div class="user-card">
    <h2>{{ user.name }}</h2>
    <p>Email: {{ user.email }}</p>
    <p>Alter: {{ user.age }} Jahre</p>
    <button @click="greet">Begrüßen</button>
  </div>
</template>

<script>
export default {
  name: 'UserCard',
  props: {
    user: {
      type: Object,
      required: true
    }
  },
  methods: {
    greet() {
      alert('Hallo, ' + this.user.name + '!');
    }
  }
}
</script>

<style scoped>
.user-card {
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}
</style>

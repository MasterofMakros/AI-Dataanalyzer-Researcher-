# Ruby Test File 1: Classes
# Expected: Extract class definitions

class BankAccount
  attr_reader :balance, :owner
  
  def initialize(owner, initial_balance = 0)
    @owner = owner
    @balance = initial_balance
    @transactions = []
  end
  
  def deposit(amount)
    @balance += amount
    @transactions << { type: :deposit, amount: amount, date: Time.now }
  end
  
  def withdraw(amount)
    raise "Insufficient funds" if amount > @balance
    @balance -= amount
    @transactions << { type: :withdraw, amount: amount, date: Time.now }
  end
  
  def statement
    puts "Kontostand fÃ¼r #{@owner}: #{@balance} EUR"
  end
end

account = BankAccount.new("Anna Schmidt", 1000)
account.deposit(500)
account.statement

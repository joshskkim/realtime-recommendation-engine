const CircuitBreaker = require('../src/circuit-breaker');

describe('Circuit Breaker', () => {
  let breaker;

  beforeEach(() => {
    breaker = new CircuitBreaker('test-service', 3, 1000);
  });

  it('should allow calls when circuit is closed', async () => {
    const fn = jest.fn().mockResolvedValue('success');
    
    const result = await breaker.call(fn);
    
    expect(result).toBe('success');
    expect(breaker.state).toBe('CLOSED');
  });

  it('should open circuit after threshold failures', async () => {
    const fn = jest.fn().mockRejectedValue(new Error('fail'));
    
    for (let i = 0; i < 3; i++) {
      try {
        await breaker.call(fn);
      } catch (e) {
        // Expected to fail
      }
    }
    
    expect(breaker.state).toBe('OPEN');
    
    // Should reject immediately when open
    await expect(breaker.call(fn)).rejects.toThrow('Circuit breaker is OPEN');
  });

  it('should transition to half-open after timeout', async () => {
    const fn = jest.fn()
      .mockRejectedValueOnce(new Error('fail'))
      .mockRejectedValueOnce(new Error('fail'))
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValue('success');
    
    // Open the circuit
    for (let i = 0; i < 3; i++) {
      try {
        await breaker.call(fn);
      } catch (e) {
        // Expected
      }
    }
    
    expect(breaker.state).toBe('OPEN');
    
    // Wait for timeout
    await new Promise(resolve => setTimeout(resolve, 1100));
    
    // Should transition to half-open and succeed
    const result = await breaker.call(fn);
    expect(result).toBe('success');
    expect(breaker.state).toBe('CLOSED');
  });
});
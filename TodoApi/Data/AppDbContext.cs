using Microsoft.EntityFrameworkCore;
using TodoApi.Models;

namespace TodoApi.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<Todo> Todos { get; set; }

    // Rent
    public DbSet<Tenant> Tenants { get; set; }
    public DbSet<MonthlyBill> MonthlyBills { get; set; }
    public DbSet<Payment> Payments { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Computed columns stored in DB for EF queries
        modelBuilder.Entity<MonthlyBill>()
            .Property(b => b.TotalPaid)
            .HasDefaultValue(0);

        // Precision for decimals
        modelBuilder.Entity<Tenant>().Property(t => t.MonthlyRent).HasPrecision(10, 2);
        modelBuilder.Entity<MonthlyBill>().Property(b => b.RentAmount).HasPrecision(10, 2);
        modelBuilder.Entity<MonthlyBill>().Property(b => b.ElectricityUnits).HasPrecision(10, 2);
        modelBuilder.Entity<MonthlyBill>().Property(b => b.ElectricityRate).HasPrecision(10, 2);
        modelBuilder.Entity<MonthlyBill>().Property(b => b.ExtraFees).HasPrecision(10, 2);
        modelBuilder.Entity<MonthlyBill>().Property(b => b.TotalPaid).HasPrecision(10, 2);
        modelBuilder.Entity<Payment>().Property(p => p.AmountPaid).HasPrecision(10, 2);
    }
}
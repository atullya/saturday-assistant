using System;
using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using TodoApi.Models;
using TodoApi.DTOs;
using TodoApi.Data;

namespace TodoApi.Repositories
{
    public class RentRepository : IRentRepository
    {
        private readonly AppDbContext _context;

        public RentRepository(AppDbContext context)
        {
            _context = context;
        }
        // ── Tenants ──────────────────────────────────────────────

        public async Task<IEnumerable<Tenant>> GetAllActiveTenantsAsync() =>
            await _context.Tenants.Where(t => t.IsActive).ToListAsync();

        public async Task<IEnumerable<Tenant>> GetArchivedTenantsAsync() =>
            await _context.Tenants.Where(t => !t.IsActive).ToListAsync();

        public async Task<Tenant?> GetTenantByIdAsync(int id) =>
            await _context.Tenants.FindAsync(id);

        public async Task<Tenant> AddTenantAsync(Tenant tenant)
        {
            _context.Tenants.Add(tenant);
            await _context.SaveChangesAsync();
            return tenant;
        }

        public async Task<Tenant?> UpdateTenantAsync(int id, UpdateTenantDto dto)
        {
            var tenant = await _context.Tenants.FindAsync(id);
            if (tenant == null) return null;

            if (dto.Phone != null) tenant.Phone = dto.Phone;
            if (dto.EmergencyContact != null) tenant.EmergencyContact = dto.EmergencyContact;
            if (dto.RoomNumber != null) tenant.RoomNumber = dto.RoomNumber;
            if (dto.MonthlyRent.HasValue) tenant.MonthlyRent = dto.MonthlyRent.Value;

            await _context.SaveChangesAsync();
            return tenant;
        }

        public async Task<bool> ArchiveTenantAsync(int id)
        {
            var tenant = await _context.Tenants.FindAsync(id);
            if (tenant == null) return false;

            tenant.IsActive = false;
            await _context.SaveChangesAsync();
            return true;
        }

        // ── Bills ────────────────────────────────────────────────

        public async Task<MonthlyBill> CreateBillAsync(MonthlyBill bill)
        {
            _context.MonthlyBills.Add(bill);
            await _context.SaveChangesAsync();
            return bill;
        }

        public async Task<MonthlyBill?> GetBillAsync(int tenantId, int month, int year) =>
            await _context.MonthlyBills
                .Include(b => b.Tenant)
                .FirstOrDefaultAsync(b => b.TenantId == tenantId
                                       && b.Month == month
                                       && b.Year == year);

        public async Task<IEnumerable<MonthlyBill>> GetDuesAsync() =>
            await _context.MonthlyBills
                .Include(b => b.Tenant)
                .Where(b => b.Tenant.IsActive && b.TotalPaid < (b.RentAmount + b.ElectricityUnits * b.ElectricityRate + b.ExtraFees))
                .ToListAsync();

        public async Task<MonthlySummaryDto> GetMonthlySummaryAsync(int month, int year)
        {
            var bills = await _context.MonthlyBills
                .Include(b => b.Tenant)
                .Where(b => b.Month == month && b.Year == year && b.Tenant.IsActive)
                .ToListAsync();

            return new MonthlySummaryDto
            {
                Month = month,
                Year = year,
                TotalTenants = bills.Count,
                TotalDue = bills.Sum(b => b.TotalDue),
                TotalCollected = bills.Sum(b => b.TotalPaid),
                TotalRemaining = bills.Sum(b => b.RemainingDue),
                Bills = bills.Select(MapBillToDto).ToList()
            };
        }

        // ── Payments ─────────────────────────────────────────────

        public async Task<Payment> RecordPaymentAsync(Payment payment)
        {
            _context.Payments.Add(payment);

            // Update TotalPaid on the bill
            var bill = await _context.MonthlyBills.FindAsync(payment.MonthlyBillId);
            if (bill != null) bill.TotalPaid += payment.AmountPaid;

            await _context.SaveChangesAsync();
            return payment;
        }

        public async Task<IEnumerable<Payment>> GetPaymentHistoryAsync(int tenantId) =>
            await _context.Payments
                .Include(p => p.Tenant)
                .Include(p => p.MonthlyBill)
                .Where(p => p.TenantId == tenantId)
                .OrderByDescending(p => p.PaymentDate)
                .ToListAsync();

        // ── Helper ───────────────────────────────────────────────

        private static BillResponseDto MapBillToDto(MonthlyBill b) => new()
        {
            Id = b.Id,
            TenantId = b.TenantId,
            TenantName = b.Tenant.FullName,
            RoomNumber = b.Tenant.RoomNumber,
            Month = b.Month,
            Year = b.Year,
            RentAmount = b.RentAmount,
            ElectricityUnits = b.ElectricityUnits,
            ElectricityRate = b.ElectricityRate,
            ElectricityAmount = b.ElectricityAmount,
            ExtraFees = b.ExtraFees,
            ExtraFeeNote = b.ExtraFeeNote,
            TotalDue = b.TotalDue,
            TotalPaid = b.TotalPaid,
            RemainingDue = b.RemainingDue
        };

    }
}
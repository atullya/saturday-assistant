using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using TodoApi.Models;
using TodoApi.DTOs;

namespace TodoApi.Repositories
{
    public interface IRentRepository
    {
        // Tenants
        Task<IEnumerable<Tenant>> GetAllActiveTenantsAsync();
        Task<IEnumerable<Tenant>> GetArchivedTenantsAsync();
        Task<Tenant?> GetTenantByIdAsync(int id);
        Task<Tenant> AddTenantAsync(Tenant tenant);
        Task<Tenant?> UpdateTenantAsync(int id, UpdateTenantDto dto);
        Task<bool> ArchiveTenantAsync(int id);

        // Bills
        Task<MonthlyBill> CreateBillAsync(MonthlyBill bill);
        Task<MonthlyBill?> GetBillAsync(int tenantId, int month, int year);
        Task<IEnumerable<MonthlyBill>> GetDuesAsync();
        Task<MonthlySummaryDto> GetMonthlySummaryAsync(int month, int year);

        // Payments
        Task<Payment> RecordPaymentAsync(Payment payment);
        Task<IEnumerable<Payment>> GetPaymentHistoryAsync(int tenantId);
    }
}
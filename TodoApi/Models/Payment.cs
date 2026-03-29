using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace TodoApi.Models
{
    public class Payment
    {
        public int Id { get; set; }
        public int TenantId { get; set; }
        public int MonthlyBillId { get; set; }
        public decimal AmountPaid { get; set; }
        public DateTime PaymentDate { get; set; } = DateTime.UtcNow;
        public string PaymentMethod { get; set; } = "Cash"; // Cash, eSewa, Bank
        public string? Note { get; set; }

        // Navigation
        public Tenant Tenant { get; set; } = null!;
        public MonthlyBill MonthlyBill { get; set; } = null!;
    }
}
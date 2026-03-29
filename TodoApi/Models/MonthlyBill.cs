using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace TodoApi.Models
{
    public class MonthlyBill
    {
        public int Id { get; set; }
        public int TenantId { get; set; }
        public int Month { get; set; }       // 1–12
        public int Year { get; set; }

        public decimal RentAmount { get; set; }

        // Electricity
        public decimal ElectricityUnits { get; set; }
        public decimal ElectricityRate { get; set; }
        public decimal ElectricityAmount => ElectricityUnits * ElectricityRate; // auto-calculated

        // Extra fees
        public decimal ExtraFees { get; set; }
        public string? ExtraFeeNote { get; set; }

        // Totals
        public decimal TotalDue => RentAmount + ElectricityAmount + ExtraFees;
        public decimal TotalPaid { get; set; }
        public decimal RemainingDue => TotalDue - TotalPaid;

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        // Navigation
        public Tenant Tenant { get; set; } = null!;
        public ICollection<Payment> Payments { get; set; } = new List<Payment>();
    }
}
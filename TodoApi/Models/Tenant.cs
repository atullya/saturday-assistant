using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace TodoApi.Models
{
    public class Tenant
    {
          public int Id { get; set; }
    public string FullName { get; set; } = string.Empty;
    public string Phone { get; set; } = string.Empty;
    public string EmergencyContact { get; set; } = string.Empty;
    public string NationalId { get; set; } = string.Empty;
    public string RoomNumber { get; set; } = string.Empty;
    public DateTime MoveInDate { get; set; }
    public decimal MonthlyRent { get; set; }
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // Navigation
    public ICollection<MonthlyBill> MonthlyBills { get; set; } = new List<MonthlyBill>();
    public ICollection<Payment> Payments { get; set; } = new List<Payment>();
    }
}
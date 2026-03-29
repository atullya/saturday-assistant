using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace TodoApi.DTOs
{
    public class TenantDtos
    {

    }
    public class CreateTenantDto
    {
        public string FullName { get; set; } = string.Empty;
        public string? Phone { get; set; } = string.Empty;
        public string? EmergencyContact { get; set; } = string.Empty;
        public string? NationalId { get; set; } = string.Empty;
        public string? RoomNumber { get; set; } = string.Empty;
        public DateTime? MoveInDate { get; set; }
        public decimal? MonthlyRent { get; set; }
    }

    public class UpdateTenantDto
    {
        public string? Phone { get; set; }
        public string? EmergencyContact { get; set; }
        public string? RoomNumber { get; set; }
        public decimal? MonthlyRent { get; set; }
    }

    public class TenantResponseDto
    {
        public int Id { get; set; }
        public string FullName { get; set; } = string.Empty;
        public string Phone { get; set; } = string.Empty;
        public string EmergencyContact { get; set; } = string.Empty;
        public string NationalId { get; set; } = string.Empty;
        public string RoomNumber { get; set; } = string.Empty;
        public DateTime MoveInDate { get; set; }
        public decimal MonthlyRent { get; set; }
        public bool IsActive { get; set; }
    }
}
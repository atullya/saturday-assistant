
public class CreateBillDto
{
    public int TenantId { get; set; }
    public int Month { get; set; }
    public int Year { get; set; }
    public decimal ElectricityUnits { get; set; }
    public decimal ElectricityRate { get; set; }
    public decimal ExtraFees { get; set; }
    public string? ExtraFeeNote { get; set; }
}

public class BillResponseDto
{
    public int Id { get; set; }
    public int TenantId { get; set; }
    public string TenantName { get; set; } = string.Empty;
    public string RoomNumber { get; set; } = string.Empty;
    public int Month { get; set; }
    public int Year { get; set; }
    public decimal RentAmount { get; set; }
    public decimal ElectricityUnits { get; set; }
    public decimal ElectricityRate { get; set; }
    public decimal ElectricityAmount { get; set; }
    public decimal ExtraFees { get; set; }
    public string? ExtraFeeNote { get; set; }
    public decimal TotalDue { get; set; }
    public decimal TotalPaid { get; set; }
    public decimal RemainingDue { get; set; }
}

public class MonthlySummaryDto
{
    public int Month { get; set; }
    public int Year { get; set; }
    public int TotalTenants { get; set; }
    public decimal TotalDue { get; set; }
    public decimal TotalCollected { get; set; }
    public decimal TotalRemaining { get; set; }
    public List<BillResponseDto> Bills { get; set; } = new();
}
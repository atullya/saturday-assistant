
public class CreatePaymentDto
{
    public int TenantId { get; set; }
    public int MonthlyBillId { get; set; }
    public decimal AmountPaid { get; set; }
    public string PaymentMethod { get; set; } = "Cash";
    public string? Note { get; set; }
}

public class PaymentResponseDto
{
    public int Id { get; set; }
    public int TenantId { get; set; }
    public string TenantName { get; set; } = string.Empty;
    public int MonthlyBillId { get; set; }
    public decimal AmountPaid { get; set; }
    public DateTime PaymentDate { get; set; }
    public string PaymentMethod { get; set; } = string.Empty;
    public string? Note { get; set; }
}
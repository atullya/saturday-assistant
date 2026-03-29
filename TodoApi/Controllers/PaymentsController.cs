using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using TodoApi.Models;
using TodoApi.Repositories;
using TodoApi.DTOs;

namespace TodoApi.Controllers
{
    [ApiController]
    [Route("api/payments")]
    public class PaymentsController : ControllerBase
    {
        private readonly IRentRepository _repo;
        public PaymentsController(IRentRepository repo) => _repo = repo;

        [HttpPost]
        public async Task<IActionResult> RecordPayment(CreatePaymentDto dto)
        {
            var payment = new Payment
            {
                TenantId = dto.TenantId,
                MonthlyBillId = dto.MonthlyBillId,
                AmountPaid = dto.AmountPaid,
                PaymentMethod = dto.PaymentMethod,
                Note = dto.Note
            };
            var recorded = await _repo.RecordPaymentAsync(payment);
            return Ok(recorded);
        }

        [HttpGet("{tenantId}")]
        public async Task<IActionResult> GetHistory(int tenantId) =>
            Ok(await _repo.GetPaymentHistoryAsync(tenantId));

    }
}
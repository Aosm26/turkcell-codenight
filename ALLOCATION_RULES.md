# Önceliklendirme ve Atama Kuralları

Bu doküman, sistemin "Case 2" kapsamında kullandığı **Minimum ve Mantıklı Önceliklendirme Kurallarını** açıklar. Her talep için hesaplanan `priority_score`, aşağıdaki ağırlıkların toplamından oluşur.

## 1. Aciliyet Seviyesi (Urgency)
Talebin oluşturulma anındaki aciliyet durumuna göre temel puan belirlenir.

| Durum | Puan | Açıklama |
| :--- | :--- | :--- |
| **HIGH** | **50** | Kritik sistem kesintileri veya acil durumlar. |
| **MEDIUM** | **30** | Standart işleyişi aksatan ama kritik olmayan durumlar. |
| **LOW** | **10** | Bilgi talebi veya düşük öncelikli istekler. |

## 2. Talep Türü (Request Type)
Talebin teknik veya operasyonel niteliğine göre ek puan verilir.

| Tür | Puan | Açıklama |
| :--- | :--- | :--- |
| **CONNECTION_ISSUE** | **40** | Bağlantı kopukluğu (En kritik teknik sorun). |
| **PAYMENT_PROBLEM** | **30** | Ödeme ve fatura sorunları. |
| **SPEED_COMPLAINT** | **25** | Hız yavaşlığı şikayetleri. |
| **STREAMING_ISSUE** | **20** | Yayın/görüntü kalitesi problemleri. |

## 3. Servis Tipi (Service)
Hizmet verilen servisin stratejik önemine göre puanlanır.

| Servis | Puan | Açıklama |
| :--- | :--- | :--- |
| **Superonline** | **20** | Fiber internet altyapısı. |
| **TV+** | **15** | Dijital yayın platformu. |
| **Paycell** | **15** | Ödeme sistemleri. |

## 4. Bekleme Süresi (Waiting Time)
Talebin sistemde ne kadar süredir beklediğine göre dinamik puan eklenir.

| Süre | Puan | Açıklama |
| :--- | :--- | :--- |
| **> 24 Saat** | **20** | 1 günü aşan talepler öncelik kazanır. |
| **> 48 Saat** | **40** | 2 günü aşan talepler daha yüksek öncelik kazanır. |

---

### Hesaplama Örneği
Eğer bir **Superonline** müşterisi, **HIGH** aciliyetle bir **CONNECTION_ISSUE** bildirirse ve talep **25 saattir** bekliyorsa:

*   **Urgency (HIGH):** 50
*   **Type (CONNECTION):** 40
*   **Service (Superonline):** 20
*   **Waiting (>24h):** 20
*   **TOPLAM SKOR:** **130**

## Let's build RAG corpus from publicly available documents  

Instead of PDFs, download the TXT versions. They are actually better for RAG because they don't contain PDF layout artifacts.

***Examples:***

| Document | URL |
| :------- | :-- |
| RFC 768 (UDP) | https://www.rfc-editor.org/rfc/rfc768.txt |
| RFC 791 (IPv4) | https://www.rfc-editor.org/rfc/rfc791.txt |
| RFC 792 (ICMP) | https://www.rfc-editor.org/rfc/rfc792.txt |
| RFC 793 (TCP) | https://www.rfc-editor.org/rfc/rfc793.txt |
| RFC 826 (ARP) | https://www.rfc-editor.org/rfc/rfc826.txt |
| RFC 1034 (DNS Concepts) | https://www.rfc-editor.org/rfc/rfc1034.txt |
| RFC 1035 (DNS Implementation) | https://www.rfc-editor.org/rfc/rfc1035.txt |
| RFC 2328 (OSPFv2) | https://www.rfc-editor.org/rfc/rfc2328.txt |
| RFC 2453 (RIP v2) | https://www.rfc-editor.org/rfc/rfc2453.txt |
| RFC 4271 (BGP-4) | https://www.rfc-editor.org/rfc/rfc4271.txt |
| RFC 4861 (IPv6 Neighbor Discovery) | https://www.rfc-editor.org/rfc/rfc4861.txt |

### Better Organization  
```
project/
│
├── docs/
│   ├── ipv4/
│   ├── ipv6/
│   ├── routing/
│   ├── transport/
│   └── application/
```

